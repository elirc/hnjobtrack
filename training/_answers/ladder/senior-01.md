# S1 rubric and reference design: teams tenancy with RLS

## Reference design (one defensible answer; others can score as well if they're argued)

- **Model**
  - `orgs(id, name, plan, created_at)`
  - `memberships(org_id, user_id, role check in ('owner','member'), primary key (org_id,user_id))`, plus an index on `(user_id)`
  - `saved_jobs` gains `org_id not null`; unique `(org_id, job_id)`; index `(org_id, saved_at desc)`
  - Personal users get a personal org (a one-member org), so there is **one** code path. Backfill in batches; see step 5.
- **RLS**
  - A helper `private.is_member(org uuid) returns boolean language sql stable security definer set search_path = ''`
    reading `memberships` for `auth.uid()`. Policies: `using (private.is_member(org_id))`.
  - Keep it in a non-exposed schema, schema-qualify everything, and don't let it take user-controlled SQL
    (`security definer` risk).
  - Alternative: an org-list claim in the JWT via Supabase's custom access token hook. Faster (no lookup per row), but
    membership changes only take effect at the next token refresh, which a removed member exploits until `exp`. The
    choice depends on your revocation SLA.
  - Wrap `auth.uid()` in `(select auth.uid())` inside policies so it's evaluated once per statement, not per row.
- **API access**
  - Per-request user-scoped PostgREST client (the INC-004 fix) for all user and org data, **plus** explicit `org_id`
    filters (both layers).
  - The service role stays only for pipeline writes to public tables and admin. Each use goes through one audited module.
- **Background jobs**
  - Digests: enumerate orgs, one job per `(org, frequency, period)` with an idempotency key, using the pipeline from S2.
  - Scope queries by `org_id` explicitly in service-role code, and add a test that fails if a digest query lacks the org filter.
  - Fair scheduling: round-robin across orgs, or cap per-org concurrency, so a 2,000-member org is chunked and doesn't
    block the rest.
  - The per-org send budget is a counter row updated atomically (`update ... set sent = sent + n where sent + n <= budget returning`).
- **Limits:** membership and saved-job caps enforced in the DB (a trigger or a check against a plan table), not only in the API.
- **Migration**
  1. Expand: add the tables and a nullable `org_id`.
  2. Create personal orgs and memberships.
  3. Backfill `org_id` in 5k-row batches.
  4. Dual-write in the API.
  5. Add `not null` (via a `not valid` check constraint, then `validate`).
  6. Switch policies.
  7. Contract: drop the user-only paths.
- **Tests**
  - Lab probes: cross-org read and write (0 rows / error), removed member (immediate with the lookup design), member vs
    owner privileges.
  - An INC-004-style concurrency test.
  - A policy-coverage check: a query over `pg_tables`/`pg_policies` asserting every table with `org_id` has RLS enabled
    and a policy for each command.
- **Observability:** a sampled audit that re-checks `org_id` of returned rows against the caller's memberships
  (log the mismatch, never serve it), plus alerting on any service-role query from request handlers.

## Rubric (10 points)

| # | Criterion | pts |
|---|---|---|
| 1 | The model covers personal users without a second code path, or argues well for keeping two | 1 |
| 2 | States how org identity reaches Postgres and the revocation trade-off | 2 |
| 3 | Keeps app-level filters as well as RLS; names what stays on the service role | 1 |
| 4 | Noisy neighbour: fair scheduling plus per-org budgets enforced atomically | 2 |
| 5 | Expand/contract with a batched backfill and constraint validation | 1 |
| 6 | Concrete tests, including RLS probes, concurrency and policy coverage | 2 |
| 7 | Detecting cross-tenant reads in production | 1 |

Auto-fail: "RLS makes app filters unnecessary", or any design where the request path uses the service role for user data without justification.
