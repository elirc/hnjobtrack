"""INC-001 regression: a token the app did not verify must never reach a service-role query.

On training/incidents/001-auth-local-jwt-decode with SUPABASE_JWT_SECRET unset (as in prod), these FAIL:
a token signed with an attacker's key reads Bob's saved jobs, and an expired token is accepted.
"""
import time

import jwt
import pytest

BOB = "22222222-2222-2222-2222-222222222222"


def forged(sub: str, exp_offset: int = 3600, key: str = "attacker-chosen-key") -> str:
    now = int(time.time())
    return jwt.encode({"sub": sub, "aud": "authenticated", "role": "authenticated",
                       "email": "x@evil.example", "iat": now, "exp": now + exp_offset}, key, algorithm="HS256")


def _prod_config(monkeypatch):
    """Prod ran with SUPABASE_JWT_SECRET unset. (On main the setting does not exist; nothing to do.)"""
    from app.core import config
    if "supabase_jwt_secret" in type(config.settings).model_fields:
        monkeypatch.setattr(config.settings, "supabase_jwt_secret", "")


@pytest.fixture
def bobs_data(fake_db):
    fake_db.tables["saved_jobs"] = [{"id": "s1", "user_id": BOB, "job_id": "j2", "saved_at": "2026-09-01T00:00:00+00:00",
                                     "notes": "bob: salary band 180k", "status": "applied"}]
    return fake_db


def test_forged_signature_is_rejected(client, bobs_data, monkeypatch):
    _prod_config(monkeypatch)
    r = client.get("/jobs/saved/all", headers={"Authorization": f"Bearer {forged(BOB)}"})
    assert r.status_code == 401, f"forged token accepted: {r.status_code} {r.text[:200]}"


def test_token_signed_with_the_project_secret_is_accepted(client, bobs_data):
    """Guards the fix: fail-closed verification must still let real users in."""
    from app.core import config
    secret = getattr(config.settings, "supabase_jwt_secret", None)
    if not secret:
        pytest.skip("this tree verifies tokens via /auth/v1/user, not locally")
    r = client.get("/jobs/saved/all", headers={"Authorization": f"Bearer {forged(BOB, key=secret)}"})
    assert r.status_code == 200 and r.json()[0]["notes"] == "bob: salary band 180k"


def test_expired_token_is_rejected(client, bobs_data, monkeypatch):
    _prod_config(monkeypatch)
    r = client.get("/jobs/saved/all", headers={"Authorization": f"Bearer {forged(BOB, exp_offset=-86400)}"})
    assert r.status_code == 401
