# HN Jobs architecture, reconstructed from the code

Every claim has an evidence path. Where the code and `README.md` disagree, the code wins, and the disagreement is noted.

## System context

```
Browser (Next.js 14 app, frontend/)
  ├─ Supabase Auth directly (password + magic link)      frontend/src/lib/supabase.ts, app/auth/*
  └─ FastAPI backend with Bearer <Supabase access token>  frontend/src/lib/api.ts:1-45
        ├─ Supabase Postgres via PostgREST (service-role key, BYPASSRLS)  backend/app/core/supabase.py:4
        ├─ Supabase Auth /auth/v1/user to validate tokens  backend/app/core/auth.py:14
        ├─ HN Algolia API (scrape)                          backend/app/services/scraper.py:5
        ├─ OpenAI gpt-4o-mini (parse)                       backend/app/services/parser.py:99
        └─ Resend (email digests)                           backend/app/services/notifications.py:95
In-process scheduler (APScheduler) inside the API process   backend/app/main.py:11-43
```

The frontend never queries tables directly; all data goes through the API (`frontend/src/lib/api.ts`). It uses
Supabase only for auth sessions, including route protection in `frontend/src/middleware.ts`.

## Components

| Component | Files | Responsibility |
|---|---|---|
| Config | `backend/app/core/config.py` | pydantic-settings from `.env`; required keys crash the import if missing |
| DB clients | `core/supabase.py` | module-level `supabase_admin` (service role) and `supabase_public` (anon, unused) |
| Auth deps | `core/auth.py` | `get_current_user` (network call to Supabase Auth), `get_optional_user` (unused), `require_admin` (X-Api-Key) |
| Routers | `api/jobs.py`, `api/saved.py`, `api/profile.py`, `api/admin.py` | HTTP surface; `saved.py` shares the `/jobs` prefix |
| Services | `services/scraper.py`, `parser.py`, `match.py`, `notifications.py` | pipeline stages and scoring |
| Schema | `supabase/schema.sql`, `supabase/migrations/20260921_job_comment_unique.sql` | 6 tables, 5 enums, RLS on the 4 user tables, `fts` generated column |

## Three request flows, file by file

**1. Browse jobs: `GET /jobs?search=python&remote=yes&page=2`**
1. `dashboard/page.tsx` builds the filters from the URL.
2. `lib/api.ts` `fetchJobs` turns them into a query string.
3. `api/jobs.py:11` `list_jobs`: validation through `Query` types and the `RemoteType`/`RoleType` enums
   (`schemas/jobs.py`).
4. It builds a PostgREST query with an embedded `hn_threads(title, month)` join and `count="exact"`, plus `range()` for
   pagination (`jobs.py:65-66`). Search goes through `or_` + `ilike` (`jobs.py:33-36`), **not** the `fts` column.
5. `_map_job` turns each row into `JobListingResponse`. `raw_text` is included in list responses.

**2. Save a job: `POST /jobs/{id}/save`**
1. `JobCard` / `JobDrawer` `onSave` → `lib/api.ts` `saveJob`.
2. `api/saved.py:16` requires `get_current_user` (`core/auth.py:6`).
3. Check-then-insert (`maybe_single` lookup, then `insert`). The DB unique `(user_id, job_id)`
   (`schema.sql:151`) is the real duplicate guard; a race surfaces as an `APIError` → 500, not 409.
4. Runs on the service-role client. Ownership = `.eq("user_id", user.id)`.

**3. Monthly pipeline (cron, day 1, 12:00 UTC)**
1. `main.py:14` `monthly_scrape_job`.
2. `scraper.py:8` finds the newest "Who is hiring" story, inserts `hn_threads` (status `pending`), fetches all comments
   page by page (`_fetch_all_comments`), and upserts top-level comments into `job_listings` with
   `on_conflict=thread_id,hn_comment_id`, `ignore_duplicates` (`scraper.py:76-97`). Status becomes `parsing`.
3. `parser.py:35` selects the rows with `parsed_at is null` and runs 20 concurrent OpenAI calls per batch, then writes
   each result. Failed calls set `is_flagged`. Status becomes `done`.
4. `notifications.py:12` (`frequency="instant"`): profiles with `notify_enabled`, the latest thread's jobs, a score per
   user, the top 10 with score > 20, Resend, then a `notifications_log` insert.

## Data model (`supabase/schema.sql`)

- `profiles(id → auth.users)`, auto-created by the `handle_new_user` trigger (`:35-46`).
- `user_preferences(user_id unique)`.
- `hn_threads(hn_post_id unique, month, status enum)`.
- `job_listings(thread_id → hn_threads on delete cascade, unique(thread_id, hn_comment_id), arrays skills/location with
  GIN indexes, generated fts)`.
- `saved_jobs(unique(user_id, job_id), status enum)`.
- `notifications_log(job_ids uuid[])`.
- There are no `updated_at` columns and no audit trail anywhere.

## Boundaries and trust

- The only authorization boundary on the API path is the Python code (the service role bypasses RLS).
- RLS protects the user tables only against direct PostgREST access with a user JWT.
- `hn_threads` and `job_listings` have no RLS at all (see the review, R1).
- LLM output crosses into the DB, the UI and email without validation (INC-005).

## Tests, build and deploy

- Tests: `backend/tests/test_scraper_recovery.py`, `test_scraper_resume.py` (unittest with hand-made fakes). No
  frontend tests. No CI config in the repo. Training tests live in `training/_answers/regression-tests/`.
- Run: `uvicorn app.main:app` (README). No Dockerfile or deploy config, so how production is deployed is
  **UNKNOWN (needs inspection)**.
- The frontend is `next build` / `next start` (`frontend/package.json`).
