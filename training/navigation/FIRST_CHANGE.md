# Before your first production change to HN Jobs

1. **The API talks to Postgres as the service role, and the service role bypasses RLS.** Every query on a user table
   must filter by the caller explicitly, and every new user table needs RLS policies *and* an explicit filter in code.
   Run `training/lab/rls/rls_lab.py` once to see what each role can do.
2. **supabase-py is synchronous, and the handlers are `async def`.** Every DB call blocks the event loop for its
   duration, and so does anything else synchronous you add (`time.sleep`, `requests`). The scheduler and the parser share
   that loop (INC-002).
3. **`.maybe_single()` returns `None` on 0 rows in this library version** (ladder J1). Don't copy the existing pattern;
   use a helper, and test against a real client with a simulated server, not a fake that agrees with you.
4. **The JSON shape is a contract with `frontend/src/types/index.ts`.** Nothing enforces it except
   `training/_answers/regression-tests/test_inc003_api_contract.py`. Any rename is an expand/contract migration (INC-003).
5. **Model output is untrusted input.** Validate it against the enums before writing (INC-005). Anything rendered as
   a link or HTML must be allow-listed or escaped.
6. **Background jobs fail silently.** An exception in the scheduler is a log line, not an alert. If your change touches
   the scrape, parse or notify path, say in the PR how a failure would become visible.
7. **Schema changes go to `supabase/migrations/` as separate, re-runnable files** (see
   `20260921_job_comment_unique.sql` for the house style: guarded, never silently deleting data). `schema.sql` is the
   from-scratch definition; keep both in sync.
8. **Know where your change runs.** Web request, cron job, admin background task, or the frontend middleware? Each has
   a different auth context and failure mode.

The minimum proof in every PR: a test that fails without the change, the RLS lab output if you touched the schema, and
a contract-test run if you touched a schema model.
