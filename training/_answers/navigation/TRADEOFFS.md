# Reference notes for the "Why?" drills

**T1: service role vs user-scoped**
- Naive: the service role everywhere, since it's simple and one client.
- Where it fails: one missed filter exposes everyone, and bugs like INC-001 get the full blast radius.
- Options:
  - A is fine for pipeline writes to public tables.
  - B puts Postgres in charge, but needs a per-request client (a shared client leaks, INC-004), and the policies must
    cover every command (P5).
  - C is flexible but easy to get wrong (claims must be set per transaction).
- Choice: B for user data, plus explicit filters; A only in the pipeline and admin.
- Tests: the RLS lab probes plus the INC-004 concurrency test.
- Monitoring: log the DB-side `auth.uid()` next to the API-side user.
- Revisit: if RLS policy cost shows in query plans (use `(select auth.uid())`).

**T2: parse at scrape time**
- A gives filterable columns and one monthly cost (about 1,000 calls; cheap with gpt-4o-mini), but a prompt change
  affects a whole month (INC-005), so it needs an eval gate plus re-parse tooling.
- B has latency on first view and can't filter.
- C is cheapest, but has two parsers to maintain.
- Keep A; add validation, evals and a `prompt_version` column so you can re-parse selectively.
- Revisit when volume or cost grows 10×.

**T3: scoring**
- A is right at ~1,000 jobs, if the projection is narrow and the call doesn't block the loop.
- B/C only when measurements say so (ladder M1).
- Whatever you pick, `get_match_breakdown` must derive from the same function (one source of truth), or users see
  contradictory numbers.

**T4: scheduler**
- A breaks with more than one worker (duplicate runs) and couples batch failures to API latency.
- B gives exactly one scheduler plus a resumable worker.
- C is simple, but runs long work inside an HTTP request.
- Choose B once there's more than one instance, or after the first INC-002-style event.

**T5: thread granularity**
- The per-thread model is honest to the source, but "daily digest" has almost nothing to show (review R9), and saved
  jobs vanish if a thread is deleted (cascade).
- Choose C (a rolling window over recent threads) and remove the cascade from `saved_jobs` (use `on delete set null`
  with a snapshot of company/role), or product-limit the digest options to monthly plus instant.
