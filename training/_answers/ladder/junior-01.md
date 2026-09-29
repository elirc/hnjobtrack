# J1 answer: `maybe_single()` returns `None`, not "a response with no data"

## Explain-before-touching: reference answers

1. **What it returns.** In postgrest-py 0.19.3, when PostgREST answers 406 / `PGRST116` ("0 rows") to a `maybe_single()`
   request, `execute()` returns **`None`**, so `result.data` raises `AttributeError`. Prove it with an experiment, not a
   doc read: an `httpx.MockTransport` returning that exact 406 body, a real `SyncPostgrestClient` pointed at it, then
   print `repr(execute())`. That was done on 2026-09-24 and it printed `None` (the snippet is in `training/lab/README.md`).
2. **Why the repo's tests pass.** `backend/tests/test_scraper_resume.py` defines its own `FakeQuery.maybe_single()` that
   returns `self`, and `execute()` returns `SimpleNamespace(data=...)`. The fake encodes the author's *assumption*,
   not the library's behaviour. That's a classic AI-generated-test smell: the fake agrees with the bug.
3. **Background call sites.**
   - `services/scraper.py:35`: the **first** scrape of every new month (no existing thread row). The cron job crashes
     before inserting the thread, so users just see no new jobs. It's only visible in the scheduler log.
   - `services/notifications.py:73`: a user with digests on but no preferences row. The crash aborts the loop, so every
     user after them gets no email that run.
4. **Options.**
   - A helper `maybe_one(q)` that wraps `execute()` and returns `res.data if res else None`: smallest change, and one place
     to fix later.
   - `.limit(1)` plus a list: works everywhere and has no special response cases, but changes every call site.
   - Upgrading supabase/postgrest: newer releases changed this behaviour; it needs a changelog check and still needs the tests.

   Any is acceptable if all call sites are covered and tested against a *real* client with a simulated server.

## Reference change (sketch)

```python
# app/core/db.py
def maybe_one(query) -> dict | None:
    res = query.maybe_single().execute()
    return res.data if res is not None else None
```

Replace each `x = ....maybe_single().execute()` + `x.data` with `maybe_one(...)`, then fix the repo's fake so
`maybe_single()` on 0 rows returns `None` (as `training/lab/fake_supabase.py` does).

## Grading

- Full marks: proves the behaviour empirically, fixes all 9 call sites, fixes the misleading fake, and notices the
  scraper/notifications impact.
- Common miss: fixing only the three endpoints in the test.
