"""Shared harness for the sealed regression tests.

Run from the backend folder of the tree you want to test (main or an incident worktree), e.g.
    cd backend && .venv/Scripts/python -m pytest ../training/_answers/regression-tests/test_inc001_jwt.py -q
(`python -m pytest` puts the current directory on sys.path, so `app` resolves to THAT tree's code.)
"""
import os
import pathlib
import sys

import pytest

# Settings() is built at import time and requires these. Fake, JWT-shaped values: supabase-py validates the shape.
for k, v in {
    "SUPABASE_URL": "http://supabase.invalid",
    "SUPABASE_ANON_KEY": "aaa.bbb.ccc",
    "SUPABASE_SERVICE_ROLE_KEY": "aaa.bbb.ddd",
    "SUPABASE_JWT_SECRET": "test-only-jwt-secret-0123456789abcdef",  # ignored by trees that lack the setting
    "DATABASE_URL": "postgresql://invalid",
    "OPENAI_API_KEY": "sk-test-never-used",
    "RESEND_API_KEY": "re_test_never_used",
}.items():
    os.environ.setdefault(k, v)

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lab"))
from fake_supabase import FakeSupabase  # noqa: E402

MODULES_USING_ADMIN = [
    "app.api.jobs", "app.api.saved", "app.api.profile", "app.api.admin",
    "app.services.notifications", "app.services.parser", "app.services.scraper",
]


@pytest.fixture
def fake_db(monkeypatch):
    """Replace get_supabase_admin everywhere it was imported by name."""
    import importlib

    db = FakeSupabase()
    for name in MODULES_USING_ADMIN:
        mod = importlib.import_module(name)
        if hasattr(mod, "get_supabase_admin"):
            monkeypatch.setattr(mod, "get_supabase_admin", lambda: db)
    return db


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)  # no `with`: the lifespan (APScheduler) must not start in tests
