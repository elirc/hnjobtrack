# S1: "HN Jobs for Teams": tenant isolation the database enforces

**Context.** Today every table is per-user, and **all** backend access goes through the service-role client, which
bypasses RLS (`backend/app/core/supabase.py:4`). So isolation depends on every query remembering
`.eq("user_id", ...)`. INC-001 and INC-004 show both ways that can go wrong. Bootcamps and recruiting agencies now
want a *team* plan:
- An organization has members with roles (owner/member).
- Saved jobs, notes and pipeline status are shared inside the org and invisible to other orgs.
- Digests are sent per org.

**Scenario.** Design and plan the rollout. Scale: 300 orgs (the largest has 2,000 members), 40,000 individual users who
must keep working unchanged.

**Operating constraints**
- Zero downtime; existing individual users become "personal orgs" or stay user-scoped (your choice, defended).
- Isolation must hold **even if a handler forgets a filter** (the database is the last line of defense).
- The monthly parse and the digests are background jobs: they must never mix orgs, and one huge org must not delay
  everyone else's digest (noisy neighbour).
- Per-org limits: max members by plan, max saved jobs, and an email send budget.

**Deliverables** (a design doc of 2–4 pages)
1. The data model: `orgs`, `memberships`, `org_id` on shared tables, and which constraints and indexes.
2. RLS policies. How is the org identity established per request? (A custom JWT claim via an auth hook, or a
   `memberships` lookup in the policy.) What does each option cost per row and per request? Where do you need `security
   definer` helpers, and what are their risks?
3. How the API talks to Postgres: a per-request user-scoped client (see the INC-004 fix) versus the service role plus an
   explicit `set_config` of the org. Which operations legitimately stay on the service role, and how do you audit them?
4. Background jobs: how does a digest job run "as" an org? How do you partition and prioritize work per org, and how do
   you enforce send budgets?
5. Migration plan (expand/contract, `curriculum/07-zero-downtime-migrations.md`), with a backfill of `org_id` in batches.
6. Tests: extend `training/lab/rls/rls_lab.py` with org probes (cross-org read/write, a removed member, a role change
   mid-session), plus a concurrency test in the style of INC-004.
7. Observability: how you would detect a cross-tenant read in production.

**Explain before touching:** which three failure modes worry you most, and which test catches each?

Rubric and reference design: `training/_answers/ladder/senior-01.md`
