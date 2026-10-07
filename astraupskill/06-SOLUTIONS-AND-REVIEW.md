# Solutions and review

## Exercise solutions

All four code solutions below were run against the current code (in a scratch copy) on 2026-10-06 and passed alongside the existing nine tests.

1. **Scope.** Both comments are rejected: a missing key gives `None`, and `"42" != 42`. No rows means the batching loop never runs, so `db.calls` stays empty. Treating missing scope as eligible would widen a remote data boundary accidentally. If Algolia returned string ids, every listing would be silently dropped and the thread would still be marked `parsing`, which is a good argument for logging the eligible-row count that `_import_comments` already returns.
2. **Duplicate in one batch.** The filter only checks text and parent, so both copies reach the same upsert. The recovery double's `setdefault` keeps `"first"`. PostgreSQL's `ON CONFLICT DO NOTHING` also skips the second row of the same statement; only `DO UPDATE` raises "command cannot affect row a second time".
3. **Graduation.** 1,001 + 2 duplicates = 1,003 eligible rows, giving batches 500, 500, 3, and 1,001 stored rows. Two workers can both read "thread exists, not done" and both upsert; the unique constraint `job_listings_thread_comment_unique` (`supabase/schema.sql:116`, migration `supabase/migrations/20260921_job_comment_unique.sql`) is what keeps one row per key.
4. **Month.** `_extract_month` parses `%B %Y` and falls back to the current month on any mismatch.
5. **Design.** (a) Flagged rows keep `parsed_at` null, so every later `parse_thread_jobs` call retries them, including the call `_run_scrape_pipeline` makes after a `done` early return (`backend/app/api/admin.py:17-21`). (b) No: once `done`, the scraper never refetches, so comments posted after the first scrape are never imported. (c) Any concrete answer with a file and line is acceptable, for example letting the scraper refetch `done` threads for the current month only.

## Rubric

Identity and uniqueness (30%), filtering and authorization scope (25%), preservation of existing data (20%), failure and retry reasoning (15%), tests that observe behavior (10%). A solution that merely changes `return` to `pass` fails because it still needs an idempotent write. A solution that deletes all children then reinserts may appear correct but risks data loss and parsed-field churn.

During review, ask the author to demonstrate the failure trace, not just show a green test: start with a durable parent and no child, invoke the retry path, inspect the recorded upsert payload, then check the SQL diff for the matching uniqueness rule. This catches an application conflict target that the database cannot honor.

## Senior review notes (verified against the code)

- **`error` status is never written.** `thread_status_enum` includes `'error'` (`supabase/schema.sql:77`), but nothing in `backend/app` writes it. An HTTP failure after the parent insert leaves the thread `pending` (proved by `test_retry_after_parent_creation_and_http_failure`). Operators cannot tell "in progress" from "crashed" from the thread row alone.
- **`done` hides late comments.** `scraper.py:43-44` returns early for `done` threads, and the cron in `backend/app/main.py:36` runs once a month. Comments added after that run are never imported.
- **Partial parse failure still reports `done`.** `parser.py:61-65` flags failed rows and continues; line 90 sets `done` unconditionally.
- **Blocking calls inside `async` functions.** `_import_comments` is `async` but contains no `await`; its Supabase `.execute()` calls (supabase-py 2.11.0 sync client, `backend/app/core/supabase.py`) block the event loop that also serves API requests while the background pipeline runs.
- **"Latest" thread depends on search ranking.** `scraper.py:11-18` uses Algolia's `/search` with `hitsPerPage: 1`. HN Search's documented `/search` endpoint sorts by relevance, while `/search_by_date` sorts by date, so the first hit is not guaranteed to be the newest thread. This is based on the public HN Search API docs and was not exercised live.

What the evidence does and does not prove: the fake tests establish the call contract, while live database merge and race behavior remain unverified.
