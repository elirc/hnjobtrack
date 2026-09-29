"""Real scraper control flow with explicit HTTP/DB doubles, not SQL integration."""
import asyncio
import importlib
import sys
import types
import unittest
from unittest.mock import patch


class Query:
    def __init__(self, db, table):
        self.db, self.table, self.operation = db, table, "select"
        self.payload, self.filters, self.options = None, {}, {}
    def select(self, *_): return self
    def eq(self, name, value): self.filters[name] = value; return self
    def maybe_single(self): return self
    def insert(self, value): self.operation = "insert"; self.payload = value; return self
    def update(self, value): self.operation = "update"; self.payload = value; return self
    def upsert(self, value, **options):
        self.operation, self.payload, self.options = "upsert", value, options
        return self
    def execute(self):
        db = self.db
        db.calls.append((self.table, self.operation, self.payload, self.options))
        if self.table == "hn_threads":
            if self.operation == "select": return types.SimpleNamespace(data=db.thread)
            if self.operation == "insert":
                db.thread = {"id": "thread-1", **self.payload}
                return types.SimpleNamespace(data=[db.thread.copy()])
            db.thread.update(self.payload)
            return types.SimpleNamespace(data=[db.thread.copy()])
        assert self.table == "job_listings" and self.operation == "upsert"
        assert self.options == {"on_conflict": "thread_id,hn_comment_id",
                                "ignore_duplicates": True, "default_to_null": False}
        db.batch_attempts += 1
        if db.fail_batch == db.batch_attempts: raise RuntimeError("batch interruption")
        for row in self.payload:
            # Model the requested contract; this does not execute PostgreSQL.
            db.rows.setdefault((row["thread_id"], row["hn_comment_id"]), row.copy())
        return types.SimpleNamespace(data=[])


class Database:
    def __init__(self, status=None):
        self.thread = None if status is None else {"id": "thread-1", "status": status}
        self.rows, self.calls = {}, []
        self.batch_attempts, self.fail_batch = 0, None
    def table(self, name): return Query(self, name)


class Response:
    def __init__(self, data): self.data = data
    def raise_for_status(self): pass
    def json(self): return self.data


class HTTP:
    def __init__(self, comments, fail_comments=False, no_story=False):
        self.comments = comments
        self.fail_comments, self.no_story = fail_comments, no_story
        self.requests = []
    async def __aenter__(self): return self
    async def __aexit__(self, *_): pass
    async def get(self, url, params):
        self.requests.append((url, params))
        if params["tags"].startswith("story"):
            hits = [] if self.no_story else [{"objectID": "42", "title": "Who is hiring? (May 2026)"}]
            return Response({"hits": hits})
        if self.fail_comments: raise RuntimeError("HTTP interruption")
        page = params["page"]
        return Response({"hits": self.comments[page*100:(page+1)*100],
                         "nbPages": max(1, (len(self.comments)+99)//100)})


def comments(count):
    return [{"objectID": str(i), "parent_id": 42, "comment_text": f"job {i}"} for i in range(count)]


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        http = types.ModuleType("httpx"); http.AsyncClient = object
        core = types.ModuleType("app.core.supabase"); core.get_supabase_admin = lambda: None
        with patch.dict(sys.modules, {"httpx": http, "app.core.supabase": core}):
            cls.scraper = importlib.import_module("app.services.scraper")
    def run_scrape(self, db, http):
        with patch.object(self.scraper, "get_supabase_admin", lambda: db), patch.object(
            self.scraper.httpx, "AsyncClient", lambda **_: http
        ):
            return asyncio.run(self.scraper.scrape_latest_thread())
    def test_new_thread_imports_pages(self):
        db, http = Database(), HTTP(comments(101))
        self.assertEqual(self.run_scrape(db, http), "thread-1")
        self.assertEqual(len(db.rows), 101)
        self.assertEqual(db.thread["status"], "parsing")
        self.assertEqual([p["page"] for _, p in http.requests if "page" in p], [0, 1])
    def test_retry_after_parent_creation_and_http_failure(self):
        db = Database()
        with self.assertRaisesRegex(RuntimeError, "HTTP interruption"):
            self.run_scrape(db, HTTP(comments(2), fail_comments=True))
        self.assertEqual(db.thread["status"], "pending")
        self.assertEqual(db.rows, {})
        self.assertEqual(self.run_scrape(db, HTTP(comments(2))), "thread-1")
        self.assertEqual(len(db.rows), 2)
        self.assertEqual(sum(t == "hn_threads" and op == "insert" for t, op, _, _ in db.calls), 1)
    def test_partial_batch_retry_preserves_parsed_fields(self):
        db = Database("pending")
        saved = {"thread_id": "thread-1", "hn_comment_id": "0", "raw_text": "original",
                 "parsed_data": {"company": "Already parsed"}, "is_parsed": True}
        db.rows[("thread-1", "0")] = saved.copy()
        db.fail_batch = 2
        with self.assertRaisesRegex(RuntimeError, "batch interruption"):
            self.run_scrape(db, HTTP(comments(501)))
        self.assertEqual(len(db.rows), 500)
        self.assertEqual(db.thread["status"], "pending")
        db.fail_batch = None
        self.run_scrape(db, HTTP(comments(501)))
        self.assertEqual(len(db.rows), 501)
        self.assertEqual(db.rows[("thread-1", "0")], saved)
        self.assertEqual(db.thread["status"], "parsing")
        self.assertEqual([len(v) for t, _, v, _ in db.calls if t == "job_listings"], [500, 1, 500, 1])
    def test_done_thread_performs_no_comment_request_or_write(self):
        db, http = Database("done"), HTTP(comments(1))
        self.assertEqual(self.run_scrape(db, http), "thread-1")
        self.assertEqual(len(http.requests), 1)
        self.assertTrue(all(op == "select" for _, op, _, _ in db.calls))
    def test_filtering_through_scrape_entry(self):
        rows = comments(1) + [{"objectID": "reply", "parent_id": 7, "comment_text": "reply"},
                               {"objectID": "empty", "parent_id": 42, "comment_text": ""}]
        db = Database("error")
        self.run_scrape(db, HTTP(rows))
        self.assertEqual(list(db.rows), [("thread-1", "0")])
    def test_no_story_does_not_create_parent(self):
        db = Database()
        self.assertIsNone(self.run_scrape(db, HTTP([], no_story=True)))
        self.assertEqual(db.calls, [])


if __name__ == "__main__": unittest.main()
