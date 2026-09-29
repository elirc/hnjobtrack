# Key points for the 20 questions

1. **Route clash.** `jobs.router` is included first (`main.py:61`), so `GET /jobs/saved` matches `/jobs/{job_id}` →
   `get_job("saved")` → 500. Fix: type `job_id` as a UUID (→ 422), declare static routes first, or give saved jobs their
   own prefix (`/me/saved`).
2. **Double click.** The check-then-insert races. The second request hits the unique `(user_id, job_id)` constraint,
   raises `APIError` and returns a 500. Better: an upsert with `on_conflict`, or catch `23505` and return 409 (or 200 if
   save is idempotent). Link `curriculum/03`.
3. **`raw_text` in lists.** It's the largest column, useless in lists, and user-generated HTML. Stop selecting it for lists
   (the list view never reads it; the drawer can fetch the detail). The TS type marks it nullable, so nothing breaks.
4. **Versioning.** Add a separate response model or a versioned route/media type with `by_alias` only there; or
   expand/contract with both keys. Contract test first.
5. **The constraint.** It makes upserts idempotent, so imports can be resumed. The guarded block is re-runnable and
   fails loudly on existing duplicates instead of deleting data.
6. **Proving index use.** Use `EXPLAIN (ANALYZE)` on the real query shape; look for a `Bitmap Index Scan on
   idx_job_listings_fts`. For users: stemming, no substring matches, `websearch` syntax.
7. **Cascade.** Saved jobs and notes silently disappear, and the saved count drops. Snapshot the key fields, or use
   `set null`.
8. **No DELETE policy.** 0 rows deleted, no error, and the API reports success. That silent failure is worse than an error.
9. **Isolation path.** Browser → Bearer → `get_current_user` (Supabase Auth call) → handler `.eq(user_id)` →
   service-role PostgREST (`BYPASSRLS`) → Postgres. The only enforcement is `.eq`.
10. **RLS can't catch auth bugs.** RLS only sees the identity it's given. With the service role it sees none; with a
    user client, a wrong identity (INC-001/004) is honoured.
11. **Stays on the service role.** Pipeline writes to `job_listings`/`hn_threads`, admin status, cross-user digest
    reads (or a `security definer` function), and `notifications_log` inserts.
12. **Claim vs lookup.** A claim is fast, but revocation waits until the token refreshes or expires. A lookup is
    immediate, costs a query per statement, and needs an index on `memberships(user_id)`.
13. **Sync inside async.** In `async def` the whole loop blocks, so nothing else runs. In `def` the call runs in the
    threadpool (40 threads by default), so the loop stays free, but beware shared per-request state (INC-004).
14. **`time.sleep`.** It blocks the loop thread. Detect it with an event-loop-lag metric, asyncio debug slow-callback
    logs, py-spy, and ruff ASYNC251 in CI.
15. **Unvalidated model output.**
    - DB write: an enum crash stalls the thread (INC-005).
    - `apply_url` into href: a phishing link through a bad scheme or domain, so allow-list the scheme.
    - Company/role into email HTML: HTML injection, so escape it.
    - Skills into search/filtering: inconsistent casing.
16. **Prompt gate.** A golden set of recorded posts; run the schema validator over the outputs; track field accuracy and
    validity rate; block the PR on regressions; store `prompt_version` per row. `curriculum/15`.
17. **Fakes.** A fake written from the author's belief passes whatever the belief is. Fake at the network edge with
    real client libraries, or record real responses; verify the fake against the real thing once.
18. **Contract test.** Parse the TS interfaces (or generate them from the OpenAPI schema), call each endpoint, and
    assert the declared keys and types. Run it in CI for both repos.
19. **Two workers.** Each worker starts its own scheduler, so every job runs twice (double emails, double OpenAI cost).
    Fix: one external scheduler (`pg_cron`), or a leader lock (`pg_try_advisory_lock`) around each job.
20. **Dedupe.** Unique `(user_id, frequency, period)` in a sends table, insert pending, send with the provider's
    idempotency key, mark it sent. The admin re-run skips rows already sent.
