"""Ladder junior-01 acceptance tests: a brand-new user's first save / first preferences / For You.

These use the REAL supabase-py + postgrest-py client (the versions pinned in backend/requirements.txt);
only the network is replaced. The PostgREST stand-in answers exactly what PostgREST 12 answers when a
`.maybe_single()` query (Accept: application/vnd.pgrst.object+json) matches no rows: HTTP 406, code PGRST116.

On main these FAIL with AttributeError: 'NoneType' object has no attribute 'data'
(postgrest-py 0.19.x returns None, not a response with data=None, for that case).
"""
import json
import types

import httpx
import pytest

ADA = "11111111-1111-1111-1111-111111111111"
JOB = {"id": "j1", "thread_id": "t1", "hn_comment_id": "42000101", "company": "Acme", "skills": ["python"],
       "location": [], "parsed_at": "2026-09-02T12:00:00+00:00"}
SAVED = {"id": "s1", "user_id": ADA, "job_id": "j1", "saved_at": "2026-09-24T12:00:00+00:00", "notes": None, "status": "saved"}


def postgrest(request: httpx.Request) -> httpx.Response:
    table = request.url.path.rsplit("/", 1)[-1]
    wants_object = "vnd.pgrst.object" in request.headers.get("accept", "")
    if request.method == "GET" and wants_object:  # nothing exists yet for this brand-new user
        return httpx.Response(406, json={"code": "PGRST116", "details": "The result contains 0 rows", "hint": None,
                                         "message": "JSON object requested, multiple (or no) rows returned"})
    if request.method == "GET" and table == "hn_threads":
        return httpx.Response(200, json=[{"id": "t1"}])
    if request.method == "GET" and table == "job_listings":
        return httpx.Response(200, json=[JOB], headers={"content-range": "0-0/1"})
    if request.method == "POST" and table == "saved_jobs":
        return httpx.Response(201, json=[SAVED])
    if request.method == "POST" and table == "user_preferences":
        body = json.loads(request.content)
        return httpx.Response(201, json=[{"id": "p1", **body}])
    return httpx.Response(501, json={"message": f"not simulated: {request.method} {request.url}"})


@pytest.fixture
def api(client, monkeypatch):
    from app.core.auth import get_current_user
    from app.main import app

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda self, req: postgrest(req))
    app.dependency_overrides[get_current_user] = lambda: types.SimpleNamespace(id=ADA, email="ada@example.com")
    yield client
    app.dependency_overrides.clear()


def test_first_save_of_a_job_succeeds(api):
    r = api.post("/jobs/j1/save", json={})
    assert r.status_code == 200 and r.json()["job_id"] == "j1"


def test_first_preferences_save_succeeds(api):
    r = api.put("/profile/preferences", json={"skills": ["python"]})
    assert r.status_code == 200 and r.json()["skills"] == ["python"]


def test_for_you_without_preferences_falls_back_to_latest_thread(api):
    r = api.get("/jobs/for-you")
    assert r.status_code == 200 and r.json()["jobs"][0]["company"] == "Acme"
