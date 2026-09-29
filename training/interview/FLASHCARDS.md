# Flashcards: HN Jobs (25)

Q | A
---|---
Which key does the backend use for Postgres, and what does that mean for RLS? | The service role (`core/supabase.py:4`); it has BYPASSRLS, so policies don't apply on the API path.
Where is user isolation actually enforced today? | The `.eq("user_id", user.id)` calls in each handler.
Which tables have no RLS in `schema.sql`? | `hn_threads`, `job_listings` (the anon key can write them: lab P7/P8).
RLS on, no policy for DELETE: owner deletes, result? | `DELETE 0`, no error (lab P5).
Why revoke grants as well as enabling RLS? | Two independent layers: a future permissive policy mistake still can't grant writes.
postgrest-py 0.19.3 `maybe_single()` with 0 rows returns? | `None`, so `.data` raises AttributeError (ladder J1).
Why do the repo's scraper tests miss that? | Their fake returns `self` from `maybe_single()`; it encodes the author's assumption.
`time.sleep` inside `async def` does what? | Blocks the whole event loop, so every request stalls (INC-002).
Symptom that suggests a blocked loop | Latency up everywhere with idle CPU.
Should `JSONDecodeError` be retried at temperature 0.1? | No: near-deterministic, so retries just cost money.
Why did the camelCase PR break reads but not writes? | `populate_by_name` affects input only; FastAPI serializes responses by alias.
How did INC-003 turn into data loss? | The profile form loaded half-empty and re-submitted `excluded_companies: []`.
What catches INC-003-style breaks? | A consumer-driven contract test against `frontend/src/types/index.ts`.
`client.postgrest.auth(token)`: new client or mutation? | Mutation of the shared session headers.
Why did INC-004 leak only under load? | The header was set in the dependency (event loop) and read later in the threadpool; another request overwrote it in between.
Defense in depth for user rows means… | Explicit filters AND RLS through a per-request user client, never one instead of the other.
What caused INC-005's thread to stall at 214? | One out-of-enum model answer raised during the write loop; the function aborted.
Was INC-005's bug in the prompt PR? | It triggered it; the missing validation and per-row isolation were already on main.
The validation boundary for model output is… | A pydantic model with the DB enums, before any write, render or email.
Where does unvalidated model text reach the UI or email? | `apply_url` in the drawer's href; company/role in digest HTML.
Search builds what from user input? | A PostgREST `or=(...)` filter expression, which is injection-class (ladder M2).
Which index exists but is unused? | `idx_job_listings_fts` on the generated `fts` column.
What happens with 2 uvicorn workers? | Two APScheduler instances, so every cron job and digest runs twice.
What does a manual `/admin/scrape` do to instant subscribers? | Emails them again (`admin.py:21`, no dedupe).
The daily digest is nearly always empty because… | It filters the latest monthly thread by `parsed_at` within the last 24 h.
