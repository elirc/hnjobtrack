# INC-001: "I can read other people's saved jobs"

**Branch:** `training/incidents/001-auth-local-jwt-decode` · **Severity:** SEV-1 (confidentiality) · **Time box:** 45 min

## What on-call sees

Tuesday 09:12, the security inbox gets this:

> Hi, I think your API has an authentication problem. A bearer token your auth service never issued was accepted by
> `GET /jobs/saved/all`, and the response contained the saved jobs and private notes of user `2222…2222`. Details went
> to your security contact. I haven't kept any data. Responsible-disclosure deadline: 30 days.

The API access log for the PoC request:

```
2026-09-22T08:57:41Z  GET /jobs/saved/all  200  23ms  ua=python-httpx/0.28.1  ip=203.0.113.77
2026-09-22T08:57:52Z  GET /profile/preferences  200  19ms  ua=python-httpx/0.28.1  ip=203.0.113.77
```

Supabase Auth logs show **no** `/auth/v1/user` call from that IP, and no sign-in for user `2222…2222` from it.

Last week's dashboard excerpt:

| metric | before Sep 17 deploy | after |
|---|---|---|
| `/jobs/for-you` p95 | 410 ms | 160 ms |
| Supabase Auth `GET /auth/v1/user` calls/day | ~48,000 | ~40 |
| 401 responses/day | ~310 | ~12 |

Production env vars (names only): `SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL, OPENAI_API_KEY, RESEND_API_KEY, FROM_EMAIL, FRONTEND_URL, BACKEND_URL, ADMIN_API_KEY`.

## Suspect change (deployed Sep 17)

`ca5142a perf(auth): decode Supabase access token locally instead of calling /auth/v1/user per request`. Read it with
`git show ca5142a` (files: `backend/app/core/auth.py`, `backend/app/core/config.py`, `backend/requirements.txt`, `.env.example`).

## Your job

1. Reproduce it on the branch without real credentials. (`training/lab/README.md` shows how to run the API against fakes.)
2. Explain **why** the forged token worked, and why the "401s/day" line in the table should have alarmed someone.
3. Answer: did Postgres RLS protect Bob's rows here? Why or why not? (Use `supabase/schema.sql` and `backend/app/core/supabase.py`.)
4. Write the fix and a regression test that fails on this branch.
5. Write the postmortem, including what the company must now do about the disclosure.

Sealed answer: `training/_answers/incidents/001-auth-local-jwt-decode.md`
