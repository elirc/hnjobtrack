"""INC-003 regression: a consumer-driven contract test between the FastAPI responses and the
TypeScript interfaces the Next.js app actually reads (frontend/src/types/index.ts).

It parses the TS interfaces, calls each endpoint, and demands every field the frontend declares.
On training/incidents/003-camelcase-api-models this FAILS for every endpoint. On main it passes.
"""
import pathlib
import re
import types

import pytest

ADA = "11111111-1111-1111-1111-111111111111"
JOB = {
    "id": "j1", "thread_id": "t1", "hn_comment_id": "42000101", "company": "Acme", "role": "Backend Engineer",
    "role_type": "full-time", "location": ["Remote (US)"], "remote": "yes", "visa_sponsorship": False,
    "salary_min": 150000, "salary_max": 190000, "salary_currency": "USD", "skills": ["python", "postgres"],
    "description": "Payments backend", "apply_url": "https://acme.example/jobs/1", "apply_email": None,
    "equity": True, "parsed_at": "2026-09-02T12:00:00+00:00", "parse_confidence": 0.92, "raw_text": "Acme | ...",
}


def ts_fields(interface: str) -> set[str]:
    src = (pathlib.Path.cwd().parent / "frontend" / "src" / "types" / "index.ts").read_text(encoding="utf-8")
    body = re.search(r"export interface " + interface + r" \{(.*?)\n\}", src, re.S).group(1)
    return set(re.findall(r"^\s+(\w+)\??:", body, re.M))


@pytest.fixture
def api(client, fake_db):
    from app.core.auth import get_current_user
    from app.main import app

    fake_db.tables.update({
        "job_listings": [JOB],
        "saved_jobs": [{"id": "s1", "user_id": ADA, "job_id": "j1", "saved_at": "2026-09-03T08:00:00+00:00",
                        "notes": "referral from Sam", "status": "applied", "job_listings": JOB}],
        "profiles": [{"id": ADA, "email": "ada@example.com", "display_name": "Ada", "notify_enabled": True,
                      "notify_frequency": "daily"}],
        "user_preferences": [{"id": "p1", "user_id": ADA, "roles": ["backend engineer"], "locations": ["remote"],
                              "remote_only": True, "visa_sponsorship": False, "skills": ["python"],
                              "salary_min": 140000, "excluded_companies": ["Initech"]}],
    })
    app.dependency_overrides[get_current_user] = lambda: types.SimpleNamespace(id=ADA, email="ada@example.com")
    yield client
    app.dependency_overrides.clear()


def missing(payload: dict, interface: str) -> set[str]:
    return ts_fields(interface) - set(payload)


def test_job_list_matches_frontend_types(api):
    body = api.get("/jobs").json()
    assert not missing(body, "JobListResponse"), f"JobListResponse fields missing: {missing(body, 'JobListResponse')}"
    assert not missing(body["jobs"][0], "JobListing"), f"JobListing fields missing: {missing(body['jobs'][0], 'JobListing')}"


def test_saved_jobs_match_frontend_types(api):
    row = api.get("/jobs/saved/all").json()[0]
    assert not missing(row, "SavedJob"), f"SavedJob fields missing: {missing(row, 'SavedJob')}"


def test_profile_and_preferences_match_frontend_types(api):
    assert not missing(api.get("/profile").json(), "Profile")
    assert not missing(api.get("/profile/preferences").json(), "Preferences")


def test_snake_case_writes_still_accepted(api):
    """The old web client sends snake_case bodies; that must keep working through any migration."""
    r = api.put("/profile/preferences", json={"remote_only": False, "excluded_companies": ["Globex"]})
    assert r.status_code == 200
    stored = api.get("/profile/preferences").json()
    assert stored.get("excluded_companies", stored.get("excludedCompanies")) == ["Globex"]
