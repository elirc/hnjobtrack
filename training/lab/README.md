# Training lab: run things instead of guessing

Everything runs from `backend/` with the existing venv (`backend/.venv`; `pytest`, `PyJWT` and `psycopg` are
installed there). No real Supabase, OpenAI or Resend credentials are needed, and nothing here calls a paid API.

## Ask the library, not the docs (a two-minute experiment)

```python
# backend/.venv/Scripts/python, then paste:
import httpx; from postgrest import SyncPostgrestClient
c = SyncPostgrestClient("http://pgrst.local")
c.session = httpx.Client(base_url="http://pgrst.local", headers=c.session.headers, transport=httpx.MockTransport(
    lambda req: httpx.Response(406, json={"code": "PGRST116", "details": "The result contains 0 rows", "hint": None,
                                          "message": "JSON object requested, multiple (or no) rows returned"})))
print(repr(c.table("user_preferences").select("*").eq("user_id", "u1").maybe_single().execute()))
```

The 406/PGRST116 body is what PostgREST sends when a single-object request matches no rows.

## 1. API tests against fakes (`fake_supabase.py`)

`FakeSupabase` models the supabase-py query-builder calls this repo uses, over dicts. It rejects out-of-enum values like
Postgres (22P02), and `maybe_single()` on 0 rows returns `None` like the real library. It does **not** model RLS, FKs
or joins; use the RLS lab for those.

The shared harness is `training/_answers/regression-tests/conftest.py`:
- It sets fake env vars.
- It patches `get_supabase_admin` in every module that imports it (fixture `fake_db`).
- It gives you a `TestClient` without starting the scheduler (fixture `client`).

It's in `_answers/` because the tests there are sealed solutions. To write your own tests, copy the conftest into
`backend/tests/`.

```bash
cd backend
.venv/Scripts/python -m pytest ../training/_answers/regression-tests/<file>.py -q -p no:cacheprovider
```

`python -m pytest` puts the current directory on `sys.path`, so `app` is whichever tree you run it from. To test an
incident branch, run the same command from a worktree:

```bash
git worktree add ../hnjobs-inc-002 training/incidents/002-parser-retry-backoff
cd ../hnjobs-inc-002/backend
../../HNJOBTRACK/backend/.venv/Scripts/python -m pytest <absolute path to the test> -q
```

Imports are slow on this machine (30–90 s per run; the supabase/openai import is the cost). That's expected.

## 2. The RLS lab (`rls/`): what does Postgres itself enforce?

It builds a fresh database from these, in order:
1. `rls/00_supabase_shim.sql`: the `anon`/`authenticated`/`service_role` roles, `auth.uid()` from JWT claims, and
   Supabase's default grants.
2. The repo's `supabase/schema.sql`.
3. Any migrations you pass.
4. `rls/10_seed.sql`: users Ada and Bob.

Then it prints a probe table (P1–P11): each probe is a statement run as a role, and the table shows what happened.

```bash
# from the repo root; pick ONE way to get a Postgres on 127.0.0.1:55491
backend/.venv/Scripts/python training/lab/rls/rls_lab.py up            # Docker (postgres:16-alpine)
backend/.venv/Scripts/python training/lab/rls/rls_lab.py native-up     # or a local install (PG_BIN env var)
backend/.venv/Scripts/python training/lab/rls/rls_lab.py run                       # schema as-is
backend/.venv/Scripts/python training/lab/rls/rls_lab.py run my_migration.sql      # schema + your migration
backend/.venv/Scripts/python training/lab/rls/rls_lab.py down          # or native-down: ALWAYS stop it afterwards
```

Add your own probes to `PROBES` in `rls_lab.py`. Probes run inside a rolled-back transaction, so they don't affect each other.
The shim is **not** Supabase: it reproduces roles, grants and `auth.uid()` only. PostgREST's JWT verification is out of
scope: the lab assumes the token was already verified.

## 3. Recorded model output (`fixtures/`)

`parse_multirole.json` holds hand-written answers shaped like gpt-4o-mini's JSON mode, used by the INC-005 test.
Add more cases here for prompt evals. Never put real API keys or real user data in fixtures.
