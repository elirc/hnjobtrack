# INC-004 answer: correct RLS, shared client state

## Symptom

At peak times only, a few users briefly saw someone else's saved jobs; a refresh fixed it. Nobody could reproduce it by
hand. Supabase logs looked normal: authenticated role, a valid user id, 200.

## Diagnostic path

1. Intermittent, only under load, and every log line individually correct: suspect **per-request state stored somewhere
   shared** (a module-level object, a cached client, a global header), not the authorization rules.
2. `git show 0cd9732`: a module-level client (`get_supabase_public()`) gets a per-user token written into it on every
   request. Check what `postgrest.auth()` does in postgrest-py 0.19.3: it sets the `Authorization` header on the client's
   shared HTTP session. It doesn't return a new client.
3. Note the timing: the dependency that sets the header runs on the event loop, while the handlers (now plain `def`) run
   later in the threadpool. The header is read when the query is sent, possibly after another request has overwritten it.
4. Reproduce it with concurrency, not clicks: the regression test below sends 40 interleaved requests from two users.

## Root cause

- `backend/app/core/supabase.py:21-29` (branch): `get_supabase_as_user` mutates and returns a **process-wide** client, so
  identity is shared mutable state.
- `backend/app/api/saved.py:41,60,70` (branch): the explicit `.eq("user_id", ...)` filters were removed ("RLS enforces
  ownership now"). With them kept, the same race would have produced wrong-but-empty results rather than exposure.
  Update and delete by `job_id` alone have the same weakness.

RLS worked exactly as designed. It enforced the policy for whichever identity arrived, and the identity that arrived was
wrong. Defense in depth means both layers stay, not that one replaces the other.

## Fix

`training/_answers/incidents/004-fix.patch` (verified 2026-09-24: test passes):
- One client **per request**: build a new `SyncPostgrestClient` with that request's headers, as a yield-dependency that
  closes it afterwards.
- Restore the explicit `user_id` filters on every read, update and delete.
- Keep the sync `def` handlers: moving blocking I/O off the event loop was the right half of the PR.

Rollout order: (1) ship the per-request client and filters; (2) enable RLS on `hn_threads` and `job_listings` (ladder
mid-03); (3) move `user_preferences`, `profiles` and the notification-log reads to the user-scoped client one table at a
time, each with this concurrency test.

## Regression test

`training/_answers/regression-tests/test_inc004_user_scoped_client.py`: drives the real ASGI app with 40 concurrent
requests from two users, with a stand-in database that applies row rules by the token's user. Verified: the branch gives
the wrong user's data in **20/40** responses (fails); passes with the fix and on main.

## Postmortem (short)

- **Impact:** intermittent cross-user exposure of saved jobs and notes at peak times, Sep 20 onward. Which users were
  affected can't be determined from existing logs, because request logs don't link the caller to the identity that
  reached the database.
- **Why it shipped:** single-user and click tests can't see races; the review focused on RLS correctness, not on how the
  identity reached it.
- **Action items:**
  - concurrency tests for anything that carries identity
  - a lint/review rule: no per-request state on module-level objects
  - log the database-side user id next to the API-side user id, and alert on any mismatch
  - privacy and legal review for notification
