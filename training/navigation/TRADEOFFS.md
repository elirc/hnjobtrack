# Senior trade-offs in HN Jobs ("Why?" drills)

For each drill, write your own version of every step before reading the reference notes. Format:
Problem → naive approach → where it fails → options A/B/C → trade-offs → choice → failure modes → how it's tested →
how it's monitored → when to revisit.

## T1. Service-role backend vs. user-scoped database access

- **Problem:** the API needs user data. Who does the database think is asking?
- **Current choice:** the service role for everything (`core/supabase.py:4`).
- **Your task:** build the drill. Compare:
  - A: the service role plus app filters (current);
  - B: a per-request user-JWT client (the INC-004 fix);
  - C: the service role plus `set_config('request.jwt.claims', ...)` in an RPC.

  Where does each fail? How do you test isolation? When is A still right?

## T2. Parse with an LLM at scrape time vs. on demand

- **Current:** parse the whole thread once a month (`parser.py`), store structured columns.
- **Compare:**
  - A: batch at scrape (current);
  - B: parse lazily when a listing is first viewed;
  - C: a regex/heuristic parser plus the LLM only for low-confidence posts.

  Consider cost, latency, filterability (you can't filter on unparsed data), and prompt-change blast radius (INC-005).

## T3. Match scoring in Python per request

- **Current:** `services/match.py` over all of a thread's jobs per request.
- **Compare:**
  - A: Python per request (current);
  - B: a SQL function;
  - C: precomputed scores.

  Consider the source of truth for the breakdown (R17 in the review), invalidation, and scale (ladder M1).

## T4. An in-process scheduler (APScheduler) vs. an external scheduler plus a worker

- **Current:** `main.py` lifespan.
- **Compare:**
  - A: in-process (current);
  - B: `pg_cron` plus a worker;
  - C: a platform cron hitting an admin endpoint.

  Consider multiple replicas, blocking the API loop, visibility of failures, and cost (ladder S2).

## T5. Monthly-thread granularity for listings

- **Current:** `job_listings.thread_id` with a cascade delete; For You and digests look at the **latest thread only**.
- **Compare:**
  - A: per thread (current);
  - B: canonical companies/roles that persist across months, with dedupe;
  - C: keep threads but query a rolling window.

  Consider the daily/weekly digest emptiness (review R9) and saved-job links breaking when a thread is deleted.

Reference notes: `training/_answers/navigation/TRADEOFFS.md`
