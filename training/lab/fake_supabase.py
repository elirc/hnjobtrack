"""A tiny in-memory stand-in for the supabase-py query builder, for tests only.

It models the call shapes this repo uses (table/select/eq/is_/not_/order/limit/range/maybe_single/single/
insert/update/upsert/delete/execute) over plain dicts. It is NOT PostgREST: no RLS, no FK checks, no joins (a select string like
"*, job_listings(*)" returns only the base row). It DOES reject values outside the enums in
supabase/schema.sql, the way Postgres would (error 22P02). Use it to test FastAPI
wiring and Python logic; use training/lab/rls/rls_lab.py for anything the database is supposed to enforce.

    from fake_supabase import FakeSupabase
    sb = FakeSupabase({"job_listings": [{"id": "j1", "company": "Acme"}]})
    sb.table("job_listings").select("*").eq("id", "j1").single().execute().data
"""
from __future__ import annotations

import copy
import itertools
import types
import uuid
from typing import Any

_ids = itertools.count(1)


class FakeAPIError(Exception):
    """Raised where postgrest-py raises APIError (e.g. .single() with 0 rows, an invalid enum value)."""


# Mirrors the enum types in supabase/schema.sql.
ENUMS = {
    ("profiles", "notify_frequency"): {"instant", "daily", "weekly"},
    ("hn_threads", "status"): {"pending", "parsing", "done", "error"},
    ("job_listings", "remote"): {"yes", "no", "hybrid"},
    ("job_listings", "role_type"): {"full-time", "part-time", "contract", "internship"},
    ("saved_jobs", "status"): {"saved", "applied", "interviewing", "rejected", "offer"},
}


def _check_enums(table: str, row: dict) -> None:
    for (t, col), allowed in ENUMS.items():
        if t == table and row.get(col) is not None and row[col] not in allowed:
            raise FakeAPIError({"code": "22P02", "message": f'invalid input value for enum {col}_enum: "{row[col]}"'})


class _Query:
    def __init__(self, db: "FakeSupabase", table: str):
        self.db, self.table = db, table
        self.op, self.payload = "select", None
        self.filters: list[tuple[str, str, Any, bool]] = []
        self._negate_next = False
        self._order: tuple[str, bool] | None = None
        self._range: tuple[int, int] | None = None
        self._single: str | None = None
        self._count = False

    # ---- verbs
    def select(self, *_cols, count=None):
        self._count = count is not None
        return self

    def insert(self, payload):
        self.op, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.op, self.payload = "update", payload
        return self

    def upsert(self, payload, **_options):
        self.op, self.payload = "upsert", payload
        return self

    def delete(self):
        self.op = "delete"
        return self

    # ---- filters
    def _f(self, kind, col, val):
        self.filters.append((kind, col, val, self._negate_next))
        self._negate_next = False
        return self

    def eq(self, col, val): return self._f("eq", col, val)
    def is_(self, col, val): return self._f("is", col, val)
    def gte(self, col, val): return self._f("gte", col, val)
    def lte(self, col, val): return self._f("lte", col, val)

    @property
    def not_(self):
        self._negate_next = True
        return self

    def order(self, col, desc=False, **_):
        self._order = (col, desc)
        return self

    def limit(self, n):
        self._range = (0, n - 1)
        return self

    def range(self, start, end):
        self._range = (start, end)
        return self

    def maybe_single(self):
        self._single = "maybe"
        return self

    def single(self):
        self._single = "single"
        return self

    # ---- execution
    def _match(self, row):
        for kind, col, val, neg in self.filters:
            v = row.get(col)
            if kind == "eq":
                ok = v == val
            elif kind == "is":
                ok = (v is None) if val in ("null", None) else (v is val)
            elif kind == "gte":
                ok = v is not None and v >= val
            else:
                ok = v is not None and v <= val
            if ok == neg:
                return False
        return True

    def execute(self):
        self.db.calls.append((self.table, self.op))
        rows = self.db.tables.setdefault(self.table, [])
        if self.op in ("insert", "upsert", "update"):
            for r in (self.payload if isinstance(self.payload, list) else [self.payload]):
                _check_enums(self.table, r)
        if self.op in ("insert", "upsert"):
            new = self.payload if isinstance(self.payload, list) else [self.payload]
            out = []
            for r in new:
                r = {"id": str(uuid.uuid4()), **copy.deepcopy(r)}
                existing = next((x for x in rows if x["id"] == r["id"]), None)
                if existing and self.op == "upsert":
                    existing.update(r)
                    out.append(copy.deepcopy(existing))
                else:
                    r.setdefault("saved_at", "2026-09-24T12:00:00+00:00")
                    rows.append(r)
                    out.append(copy.deepcopy(r))
            return types.SimpleNamespace(data=out, count=None)
        hits = [r for r in rows if self._match(r)]
        if self.op == "update":
            for r in hits:
                r.update(copy.deepcopy(self.payload))
            return types.SimpleNamespace(data=copy.deepcopy(hits), count=None)
        if self.op == "delete":
            for r in hits:
                rows.remove(r)
            return types.SimpleNamespace(data=copy.deepcopy(hits), count=None)
        if self._order:
            col, desc = self._order
            hits.sort(key=lambda r: (r.get(col) is None, r.get(col) or ""), reverse=desc)
        total = len(hits)
        if self._range:
            hits = hits[self._range[0]: self._range[1] + 1]
        hits = copy.deepcopy(hits)
        if self._single == "maybe":
            return None if not hits else types.SimpleNamespace(data=hits[0], count=None)
        if self._single == "single":
            if len(hits) != 1:
                raise FakeAPIError("JSON object requested, multiple (or no) rows returned")
            return types.SimpleNamespace(data=hits[0], count=None)
        return types.SimpleNamespace(data=hits, count=total if self._count else None)


class FakeSupabase:
    def __init__(self, tables: dict[str, list[dict]] | None = None):
        self.tables = copy.deepcopy(tables or {})
        self.calls: list[tuple[str, str]] = []

    def table(self, name: str) -> _Query:
        return _Query(self, name)
