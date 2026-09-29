# INC-001 answer: token verification that fails open

## Symptom

An outside report says the API accepted a token it never issued and returned another user's saved jobs. The metrics
table in the brief shows a second signal: 401 responses dropped from ~310/day to ~12/day after the Sep 17 deploy.

## Diagnostic path

1. Treat the 401 drop as the alarm. Expired sessions and bad tokens didn't stop happening, so the API must have stopped
   rejecting them. (The drop in `/auth/v1/user` calls is the intended performance win.)
2. `git show ca5142a` and look for any condition around verification. A verify flag driven by config is the smell.
3. Confirm the library behaviour: in PyJWT, turning off signature verification also turns off the `exp` check.
4. Reproduce it offline with the regression test below. Don't use production and don't use real credentials.
5. Scope the exposure: look for requests whose user id has no matching Supabase Auth session. Tokens aren't logged, so
   the honest answer may be "we can't prove who else was affected".

## Root cause

- `backend/app/core/auth.py:21-27` (branch): the decode passes `settings.supabase_jwt_secret or None` as the key and
  `options={"verify_signature": bool(settings.supabase_jwt_secret)}`.
- `backend/app/core/config.py:8` (branch): `supabase_jwt_secret: str = ""`. The new setting was never added to production.

So in production the check that is missing is **signature and expiry verification**. The code fails open: a missing
config value makes it less secure, and nothing crashes or logs.

**Why RLS didn't help.** Every handler queries through `get_supabase_admin()` (`backend/app/core/supabase.py:4`, the
service-role key, which has `BYPASSRLS`). Ownership rests entirely on `.eq("user_id", user.id)`, and `user.id` comes from
the token. The policies in `supabase/schema.sql` are correct, but they only apply to requests that reach PostgREST with a
user JWT. Lab evidence: probe P10 in `training/lab/rls/rls_lab.py` (the service role sees every user's rows).

## Fix

`training/_answers/incidents/001-fix.patch` (verified 2026-09-24: 3/3 tests pass with it applied):
- The secret is a required setting (`Field(min_length=32)`), so a missing env var stops the app **at boot**.
- Always verify: pinned `algorithms=["HS256"]`, `audience="authenticated"`, `require=["exp","sub","aud"]`. No config
  switch can weaken it.
- Alternatives to weigh: verify with the project's public keys (JWKS) if the project uses asymmetric signing, or go back
  to `/auth/v1/user` with a short cache. That is slower, but revocation (logout, bans) takes effect immediately.

## Regression test

`training/_answers/regression-tests/test_inc001_jwt.py` checks three things:
- a token the project didn't sign → 401
- an expired token → 401
- a correctly signed token → 200 (guards against a "fix" that locks everyone out)

Verified results: on the branch, the first two get 200 (the test fails); on main and with the fix, they get 401.

## Postmortem (short)

- **Impact:** from Sep 17 until the fix, authenticated endpoints trusted the identity claimed in the token. Every user's
  saved jobs, notes, preferences and profile were exposed. One reporter, who disclosed responsibly.
- **Why it shipped:** a security-weakening default (`""`) is invisible in review; no test for "bad token → 401"; staging
  probably had the secret set.
- **Action items:**
  - required secrets fail boot
  - negative-auth tests in CI (bad signature, expired, wrong audience, disallowed algorithm)
  - an alert on a sudden fall in 401s
  - use a user-scoped client for user-owned tables so RLS limits the blast radius (see INC-004 and ladder `senior-01`)
  - notification and disclosure decision with legal, and thank the reporter
- **Lesson:** a performance PR that touches auth gets a security review, and config that weakens a check must never have a default.
