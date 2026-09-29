# INC-004: "Someone else's notes showed up on my Saved page, then went away"

**Branch:** `training/incidents/004-saved-jobs-user-scoped-rls` · **Severity:** SEV-1 (confidentiality, intermittent) · **Time box:** 60 min

## What on-call sees

Three tickets in two days, all at busy times (Monday 09:00–10:00 UTC, right after the weekly digest email goes out):

> I opened Saved and saw a job I never saved with the note "salary band 180k, recruiter = Dana". I refreshed and it was gone.

> The Saved page briefly showed 14 jobs; I have 3.

Nobody on the team can reproduce it locally. Clicking around as two test users in two browsers shows correct data every time.

Supabase API logs for one of the reported requests look normal: `role=authenticated`, the right `sub` for **a** user, 200 OK.

| metric | week before Sep 20 deploy | week after |
|---|---|---|
| `/jobs/saved/all` p95 | 380 ms | 120 ms |
| event-loop lag (p99) | 240 ms | 15 ms |
| requests to PostgREST with the service-role key | 100% | 61% |

The security lead's comment on the deploy: "Finally, RLS is doing real work. Nice defense in depth."

## Suspect change (deployed Sep 20)

`0cd9732 security(saved): run saved-jobs queries as the user so RLS enforces ownership`
(`backend/app/core/supabase.py`, `backend/app/core/auth.py`, `backend/app/api/saved.py`).

## Your job

1. Explain how a request can run with the wrong user's identity when every single query is authorized by RLS.
2. Explain why two browsers clicking by hand never reproduce it, and write a test that does, every time.
3. Explain why the latency improvement and the bug arrived in the same PR, and whether both parts of the PR were good ideas.
4. Fix it without giving up RLS-as-defense-in-depth. Say which other tables should follow, and what the rollout order is.
5. Postmortem: is this reportable? Which users were exposed, and can you tell from the logs you have?

Sealed answer: `training/_answers/incidents/004-saved-jobs-user-scoped-rls.md`
