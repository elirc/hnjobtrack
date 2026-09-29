import asyncio
import importlib
import sys
import types
import unittest


class FakeQuery:
    def __init__(self, table, db):
        self.table, self.db = table, db
        self.filters = {}
        self.payload = None

    def select(self, *_args): return self
    def eq(self, key, value): self.filters[key] = value; return self
    def maybe_single(self): return self
    def insert(self, payload): self.payload = payload; return self
    def upsert(self, payload, on_conflict=None, ignore_duplicates=False, default_to_null=True):
        self.payload = payload; self.db.conflict = (on_conflict, ignore_duplicates, default_to_null); return self
    def update(self, payload): self.payload = payload; return self

    def execute(self):
        self.db.calls.append((self.table, self.payload, self.db.conflict))
        if self.table == "hn_threads" and self.payload is None:
            return types.SimpleNamespace(data=self.db.existing)
        if self.table == "hn_threads" and isinstance(self.payload, list):
            return types.SimpleNamespace(data=[{"id": "thread-new"}])
        return types.SimpleNamespace(data=[])


class FakeDB:
    def __init__(self, existing):
        self.existing, self.calls, self.conflict = existing, [], None
    def table(self, name): return FakeQuery(name, self)


class FakeClient:
    async def get(self, *_args, **_kwargs):
        return None


class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): return None
    def json(self): return self.payload


class FakeHTTPClient:
    def __init__(self, *args, **kwargs): self.comment_requests = 0
    async def __aenter__(self): return self
    async def __aexit__(self, *_args): return None
    async def get(self, _url, params=None):
        if params and params.get("tags", "").startswith("story"):
            return FakeResponse({"hits": [{"objectID": "42", "title": "Who is hiring? (May 2026)"}]})
        self.comment_requests += 1
        if self.comment_requests == 1:
            return FakeResponse({"hits": [{"objectID": "c1", "parent_id": 42, "comment_text": "role"}], "nbPages": 1})
        return FakeResponse({"hits": [], "nbPages": 1})


class ResumeImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("httpx", types.SimpleNamespace(AsyncClient=object))
        core = types.ModuleType("app.core.supabase")
        core.get_supabase_admin = lambda: None
        sys.modules["app.core.supabase"] = core
        cls.scraper = importlib.import_module("app.services.scraper")

    def test_existing_thread_is_refetched_and_upserted(self):
        db = FakeDB({"id": "thread-old", "status": "pending"})
        async def comments(_client, _post):
            return [{"objectID": "c1", "parent_id": 42, "comment_text": "role"}]
        old = self.scraper._fetch_all_comments
        self.scraper._fetch_all_comments = comments
        old_sb = self.scraper.get_supabase_admin
        try:
            old_client = self.scraper.httpx.AsyncClient
            self.scraper.httpx.AsyncClient = FakeHTTPClient
            self.scraper.get_supabase_admin = lambda: db
            async def run():
                return await self.scraper.scrape_latest_thread()
            self.assertEqual(asyncio.run(run()), "thread-old")
        finally:
            self.scraper._fetch_all_comments = old
            self.scraper.httpx.AsyncClient = old_client
            self.scraper.get_supabase_admin = old_sb
        self.assertEqual(db.conflict, ("thread_id,hn_comment_id", True, False))
        job_calls = [call for call in db.calls if call[0] == "job_listings"]
        self.assertEqual(job_calls[0][1][0]["hn_comment_id"], "c1")

    def test_completed_thread_is_not_refetched(self):
        db = FakeDB({"id": "thread-done", "status": "done"})
        old_client = self.scraper.httpx.AsyncClient
        old_sb = self.scraper.get_supabase_admin
        self.scraper.httpx.AsyncClient = FakeHTTPClient
        self.scraper.get_supabase_admin = lambda: db
        try:
            self.assertEqual(asyncio.run(self.scraper.scrape_latest_thread()), "thread-done")
            self.assertEqual([c for c in db.calls if c[0] == "job_listings"], [])
        finally:
            self.scraper.httpx.AsyncClient = old_client
            self.scraper.get_supabase_admin = old_sb

    def test_import_filters_nested_and_empty_comments(self):
        db = FakeDB(None)
        comments = [
            {"objectID": "top", "parent_id": 42, "comment_text": "ok"},
            {"objectID": "nested", "parent_id": 7, "comment_text": "skip"},
            {"objectID": "empty", "parent_id": 42, "comment_text": ""},
        ]
        self.assertEqual(asyncio.run(self.scraper._import_comments(db, "t", "42", comments)), 1)
        self.assertEqual(db.calls[0][1][0]["hn_comment_id"], "top")


if __name__ == "__main__":
    unittest.main()
