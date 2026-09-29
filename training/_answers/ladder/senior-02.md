# S2 rubric: the pipeline out of the API

**Reference shape**
- **Components.** One worker process (`python -m app.worker`) plus a Postgres-backed queue (a `jobs` table with
  `for update skip locked`, or pgmq/pg-boss-style).
  - Scheduling: Supabase `pg_cron` inserts the monthly and digest jobs, so there's exactly one scheduler and API
    replicas don't matter.
  - The API only enqueues (`POST /admin/scrape` → insert a job, return 202 plus a job id).
- **State.**
  - `hn_threads.status`: pending → scraping → parsing → done/error.
  - Per listing: `parse_status` (pending/parsed/flagged/failed) plus `attempts`, `last_error`, and a lease/`locked_until`.
  - Resumable by construction: every stage selects "not yet done" rows.
- **Retries by failure class.**
  - 429 / timeout: backoff with jitter, honouring `Retry-After`.
  - Invalid output: no retry; flag it (INC-005).
  - DB error: retry a few times, then park it.
  - Poison items go to `failed`, surfaced on `/admin/status` and alerted on.
- **Digest idempotency.** Unique key `(user_id, frequency, period_start)` in a `digest_sends` table. Insert the row
  `pending` first; the send uses the provider's idempotency key (Resend supports an `Idempotency-Key` header); then mark
  it sent. If the insert or update fails after the provider accepted, the retry reuses the same key and the provider
  dedupes. Link `curriculum/02-idempotency.md` and `curriculum/01-transactional-outbox.md`.
- **Cost.**
  - Estimate tokens (length/4 as a heuristic, or tiktoken) before each call.
  - A monthly budget row updated atomically; stop parsing and alert at 100%.
  - Monthly bulk parsing fits the Batch API (lower price, 24 h window).
- **Rollout.**
  1. Ship the worker behind a flag, in shadow mode: it records what it *would* process.
  2. Compare with the in-process run for one month.
  3. Flip: disable the `AsyncIOScheduler` jobs.
  4. Delete the in-process scheduler in a later release.

**Rubric (10 points):**

| Criterion | pts |
|---|---|
| Exactly one scheduler, justified | 2 |
| Resumable per-item state | 2 |
| Retry matrix by failure class | 2 |
| Digest idempotency, including the "provider accepted, log failed" window | 2 |
| Cost cap and observability | 1 |
| Safe side-by-side rollout | 1 |

Common miss: re-running `send_digest_notifications()` from the admin endpoint (the current `admin.py:21` behaviour) with no dedupe key.
