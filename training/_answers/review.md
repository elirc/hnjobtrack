# Model review of HN Jobs `main` (2bb1f26)

Ranked by production severity. **[AI]** marks a typical old-AI-generated smell. "Verified" means it was run on
2026-09-24; otherwise the finding comes from reading the code.

## Critical / high

**R1. The public anon key can modify listings and threads. (critical, verified)**
- Where: `supabase/schema.sql:79-137` has no `enable row level security` on `hn_threads` or `job_listings`. Supabase
  grants table privileges to `anon`/`authenticated` by default.
- Impact: anyone with the key shipped to every browser can change listings, including Apply links, or insert threads
  that the "latest thread" queries then prefer.
- Proof: RLS lab probes P7 (`UPDATE 1`) and P8 (`INSERT 0 1`).
- Fix: the ladder mid-03 migration (verified: both become 42501, and reads still work).

**R2. Optional-row lookups crash for new users and in background jobs. (high, verified)**
- Where: 9 call sites of `.maybe_single().execute().data` (list in ladder J1).
- Why: postgrest-py 0.19.3 returns `None` when no row matches.
- Impact: a job's first save, a user's first preferences save and For You without preferences return 500. The first
  scrape of a new month (`scraper.py:35`) and digests for users without preferences (`notifications.py:73`) crash.
- Proof: `test_junior01_first_time_user.py` gives 3/3 `AttributeError` on main.
- **[AI]** The repo's own fake (`backend/tests/test_scraper_resume.py:16`) returns `self` from `maybe_single()`, so the
  tests encode the wrong assumption.

**R3. User-data isolation depends entirely on hand-written filters. (high, design)**
- Where: every handler uses the service-role client (`core/supabase.py:4`, `BYPASSRLS`). The correct RLS policies in
  `schema.sql` protect nothing on the API path.
- Impact: one forgotten `.eq("user_id", ...)` exposes all users. INC-001 and INC-004 are two ways this goes wrong.
- Fix: ladder S1, the INC-004 fix (a per-request user client plus explicit filters).

**R4. Search builds PostgREST filter syntax from user input. (high)**
- Where: `api/jobs.py:34-36` interpolates `search` into `or_(...)`.
- Impact: characters that are structural in the filter grammar break queries (500s) or change their meaning.
  The same class as SQL injection.
- Fix: ladder M2 (full-text search on `fts`, passed as a value).

**R5. Model output is written and rendered with no validation. (high)**
- Where: `services/parser.py:67-88` writes the parsed JSON field by field.
- Impact:
  - Out-of-enum values crash the whole thread (INC-005 shows the bug is latent on main; its test fails on main).
  - `apply_url` goes straight into an `<a href>` (`JobDrawer.tsx:239-241`), so only `http(s)` should be allowed.
  - `company`/`role` from untrusted HN text are put unescaped into email HTML (`notifications.py:134-150`), which
    allows HTML injection into our emails. Use `html.escape`.

**R6. An open redirect after login. (high)**
- Where: `frontend/src/app/auth/callback/route.ts:8,31` does `new URL(redirect, request.url)` with an unchecked query
  parameter; an absolute URL redirects off-site. `login/page.tsx:12,38,52` passes the same value on.
- Impact: phishing that starts from a genuine login link.
- Fix: allow only same-origin relative paths (starts with `/`, not `//`).

**R7. The whole pipeline runs inside the web process and blocks it. (high)**
- Where: `AsyncIOScheduler` in `main.py:11-43`; `BackgroundTasks` in `admin.py:13`; sync supabase-py calls inside
  every `async def` handler and service.
- Impact:
  - DB latency blocks the event loop for everyone.
  - With several workers or instances, each cron job runs N times.
  - Failures only appear as scheduler log lines.
- Fix: ladder S2.

## Medium

**R8. Re-running the scrape re-sends "instant" digests to everyone. (medium)**
- Where: `admin.py:21` calls `send_digest_notifications()` with the default `frequency="instant"`.
  `notifications_log` is written but never checked.
- Impact: every manual retry emails every instant subscriber again.

**R9. Daily and weekly digests are almost always empty. (medium)**
- Where: `notifications.py:54-60` filters jobs of the **latest monthly thread** by `parsed_at` within the last 24 h / 7 days.
- Impact: after the first day or week of the month, nothing qualifies.
- **[AI]** The README describes the feature as working.

**R10. Admin key defaults and comparison. (medium)**
- `config.py:14` defaults `admin_api_key` to `"changeme"`: if the env var is missing, admin endpoints are protected by
  a public default.
- `auth.py:33` uses `!=` instead of a constant-time compare (low on its own).
- Fix: make the setting required and compare with `hmac.compare_digest`.

**R11. `/jobs/{id}` returns 500 for missing or malformed ids. (medium)**
- Where: `jobs.py:128,135` (`.single()`). See ladder J2.

**R12. `/jobs/saved/all` works only because of router order. (medium, fragile)**
- Where: `main.py:61-64`. `GET /jobs/saved` falls into `get_job`.

**R13. For You loads a whole thread including `raw_text`, then scores it in Python. (medium, performance)**
- Where: `jobs.py:102-122`. See ladder M1.

**R14. No delete policy on `user_preferences`. (medium, verified P5)**
- Reset or delete can't work once the API goes through RLS.

**R15. Emails and exceptions go to stdout with `print`. (medium, operability/PII)**
- Where: `notifications.py:113`.
- Impact: email addresses end up in logs; there is no structured logging and no metric for send failures.

**R16. Docs vs reality. [AI] (medium)**
- The README claims "PostgreSQL tsvector indexing" (not used, see R4) and "JWT verification" (it's a network call).
- "Comments are processed in batches of 20 concurrent requests" is true but presented as a feature, with no rate-limit
  handling (INC-002 background).

## Low

**R17. `get_match_breakdown` isn't the same algorithm as the score.**
- `skill_score` is a count, not points, and the role match ignores the partial-word rule (`match.py:83-117`), so the
  drawer can disagree with the card.

**R18. The profile page swallows load errors.**
- `profile/page.tsx:66` logs and renders a half-filled form that then saves over real data (INC-003 shows the damage).

**R19. Accessibility gaps.**
- `JobCard` is a clickable `div`; buttons are hover-only; the drawer has no dialog semantics or focus management; the
  breakdown uses colour only. See ladder M4.

**R20. Tests.**
- Two backend test files, both on the scraper, both with fakes built on assumptions. No API tests, no frontend tests,
  no CI config. **[AI]**

**R21. The auth callback ignores `exchangeCodeForSession` errors (`route.ts:28`).**
- An expired magic link lands on the dashboard logged out, with no message.

## What's good (say it in the interview too)

- The upsert with `on_conflict` and `ignore_duplicates` in the scraper makes imports resumable.
- The unique `(thread_id, hn_comment_id)` constraint with a careful migration that refuses to delete duplicates.
- Correct per-user RLS policies on the user tables.
- DOMPurify on `raw_text`.
- Typed enums on both sides.
