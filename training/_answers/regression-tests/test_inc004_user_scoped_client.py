"""INC-004 regression: under concurrent traffic, every user sees only their own saved jobs.

Production shape: ONE event loop, sync handlers in the threadpool, many users at once. The test drives the
real ASGI app with 40 concurrent requests (Ada and Bob interleaved) through httpx.ASGITransport.

The database side is simulated faithfully for this question: a PostgREST stand-in (patched into httpx)
applies "RLS" by reading the `sub` of the Bearer token on each request, exactly as Supabase does after it
verifies the JWT, and takes 30 ms per query. On main (service-role client + explicit user_id filter) the
in-memory fake is used instead; both paths must isolate users.

On training/incidents/004-saved-jobs-user-scoped-rls this FAILS (users receive each other's rows).
"""
import asyncio
import base64
import json
import time
import types

import httpx
import pytest

ADA = "11111111-1111-1111-1111-111111111111"
BOB = "22222222-2222-2222-2222-222222222222"
ROWS = {
    ADA: {"id": "s1", "user_id": ADA, "job_id": "j1", "saved_at": "2026-09-03T08:00:00+00:00", "notes": "ada: referral from Sam", "status": "saved"},
    BOB: {"id": "s2", "user_id": BOB, "job_id": "j2", "saved_at": "2026-09-04T08:00:00+00:00", "notes": "bob: salary band 180k", "status": "applied"},
}


def token_for(sub: str) -> str:
    """Unsigned, JWT-shaped. Authentication itself is overridden below: this test is about isolation, not auth."""
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    return f"{enc({'alg': 'HS256', 'typ': 'JWT'})}.{enc({'sub': sub, 'role': 'authenticated'})}.sig"


def sub_of(bearer: str) -> str | None:
    try:
        payload = bearer.split(" ", 1)[1].split(".")[1]
        return json.loads(base64.urlsafe_b64decode(payload + "==")).get("sub")
    except Exception:
        return None  # e.g. the anon key: RLS returns nothing


def postgrest_with_rls(request: httpx.Request) -> httpx.Response:
    time.sleep(0.03)
    sub = sub_of(request.headers.get("authorization", ""))
    if request.method == "GET" and request.url.path.endswith("/saved_jobs"):
        rows = [dict(ROWS[sub], job_listings=None)] if sub in ROWS else []
        return httpx.Response(200, json=rows)
    return httpx.Response(501, json={"message": f"not simulated: {request.method} {request.url.path}"})


@pytest.fixture
def app_under_test(fake_db, monkeypatch):
    from app.core.auth import get_current_user
    from app.main import app

    fake_db.tables["saved_jobs"] = [dict(r) for r in ROWS.values()]  # used by trees that query as service role
    # Any real supabase-py/postgrest client (shared or per-request) talks HTTP through httpx.HTTPTransport:
    # route all of it to the RLS-applying stand-in.
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, request: postgrest_with_rls(request))

    from fastapi import Header

    async def override(authorization: str = Header(None)):
        return types.SimpleNamespace(id=sub_of(authorization), email="x@example.com")

    app.dependency_overrides[get_current_user] = override
    yield app
    app.dependency_overrides.clear()


async def _burst(app, n: int = 40):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as c:
        users = [ADA if i % 2 == 0 else BOB for i in range(n)]
        resps = await asyncio.gather(*[
            c.get("/jobs/saved/all", headers={"Authorization": f"Bearer {token_for(u)}"}) for u in users
        ])
    return list(zip(users, resps))


def test_concurrent_users_never_see_each_others_saved_jobs(app_under_test):
    results = asyncio.run(_burst(app_under_test))
    leaks = []
    for user, r in results:
        assert r.status_code == 200, r.text[:200]
        owners = {row["notes"].split(":")[0] for row in r.json()}
        expected = "ada" if user == ADA else "bob"
        if owners != {expected}:
            leaks.append((expected, sorted(owners)))
    assert not leaks, f"{len(leaks)}/{len(results)} responses had the wrong user's data, e.g. {leaks[:3]}"
