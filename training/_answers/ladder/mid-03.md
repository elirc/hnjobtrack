# M3 answer: RLS on the public tables

**Lab on main (verified 2026-09-24, native Postgres 18, `training/lab/rls/rls_lab.py run`):**

| probe | main | after the reference migration |
|---|---|---|
| P5 ada deletes her own preferences | DELETE 0 | DELETE 1 |
| P7 anon updates a listing | **UPDATE 1** | ERROR 42501 |
| P8 anon inserts a thread | **INSERT 0 1** | ERROR 42501 |
| P11 anon reads listings | count=2 | count=2 |
| P1–P4, P6, P9, P10 | unchanged: user rows isolated, service role sees all | unchanged |

1. **Surprises and impact.** Anyone holding the public key could change the listings every user sees, including where
   the Apply button points, and could insert fake threads that the "latest thread" queries then prefer
   (`order("month", desc=True)`). That is an integrity and phishing risk for every user. P5 is a functional gap.
2. **No policy for a command.** With RLS on and no policy for that command, the command sees and changes 0 rows. For
   INSERT it's an error (`new row violates row-level security policy`). Also revoke write privileges: then the failure
   is an explicit permission error, and a future permissive policy added by mistake still can't grant writes (two
   independent layers).
3. **Service role.** It has `BYPASSRLS`, and the backend holds that key server-side only.
4. **Rollout order** (if the frontend read listings directly): add the SELECT policy **before** or in the same
   transaction as `enable row level security`, otherwise public reads return 0 rows.

Reference migration: `training/_answers/ladder/mid-03-lock-down-public-tables.sql`.
