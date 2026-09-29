# INC-002 answer: a blocking sleep inside `async def` froze the only event loop

## Symptom

For 33 minutes after the monthly cron started (Oct 1, 12:00 UTC), every endpoint timed out, `/health` included, while
CPU stayed at 4–7%. The parser logged about 1,900 retry lines, and parse quality was the best the team had seen.

## Diagnostic path

1. Correlate: the outage window matches `monthly_scrape_job` (`backend/app/main.py:14`, cron day=1 12:00) exactly.
2. Latency up across the board, CPU idle: think "the event loop is blocked", not "overloaded". In Python, look inside
   `async def` for `time.sleep`, `requests.*`, sync DB clients and CPU-heavy loops.
3. `git show da7b07d` reveals `time.sleep(delay)` in the retry loop.
4. Prove it with a heartbeat coroutine that measures the longest gap between ticks while the parser runs against a fake
   OpenAI client (the regression test below). In production: an event-loop-lag metric, or asyncio debug mode's
   slow-callback warnings.

## Root cause

- `backend/app/services/parser.py:128` (branch): `time.sleep(delay)` inside `async def _parse_single`. The parser shares
  the API's event loop (`AsyncIOScheduler` in `main.py:11`; `BackgroundTasks` in `api/admin.py:13`). While one task
  sleeps, no request handler and no other parse task can run. The backoffs of 1/2/4/8 s per 429 add up serially over
  20-wide batches. A sleeping thread uses no CPU, which explains the idle CPU.
- `parser.py:42` (branch): `json.JSONDecodeError` is in `RETRYABLE`. At `temperature=0.1` a malformed answer is close to
  deterministic, so retrying it only multiplies cost.
- Latent on main: the synchronous supabase-py calls inside `async def` also block the loop, for milliseconds per call.

## Fix

`training/_answers/incidents/002-fix.patch` (verified 2026-09-24: 2/2 tests pass):
- Replace the sleep with `await asyncio.sleep(2**attempt + random.uniform(0, 1))`, which yields to the loop and adds jitter
  so retries don't synchronize.
- Drop `JSONDecodeError` from `RETRYABLE`; a malformed answer is flagged instead.

Still open after this fix (the answer to question 4): a fixed 20-wide `gather` ignores the rate limit. Size concurrency to
the RPM/TPM limit (a semaphore or token bucket), honour `Retry-After`, or use the Batch API for a monthly job. Longer term,
move the pipeline out of the API process. See `curriculum/14-load-backpressure-timeouts.md`.

## Regression test

`training/_answers/regression-tests/test_inc002_parser_loop.py`
- `test_parse_pipeline_does_not_block_the_event_loop`: on the branch the loop stalled for **6.13 s** with only 3 listings
  (fails). Passes on main and with the fix.
- `test_transient_429s_are_retried_not_flagged`: fails on main (the September flagging bug), passes on the branch and
  with the fix. Keep both, so neither regression can come back while fixing the other.

## Postmortem (short)

- **Impact:** 33 min of full API unavailability. No data loss.
- **Why it shipped:** the PR was judged only by its goal metric (flag rate); nothing tests the parser and HTTP serving
  together; no lint rule for blocking calls in async code.
- **Action items:**
  - alert on event-loop lag
  - enable ruff's `ASYNC` rules
  - run the batch pipeline in a separate worker
  - make concurrency rate-limit-aware
  - add a runbook line: "slow everywhere with idle CPU → blocked loop"
