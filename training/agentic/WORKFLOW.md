# Agentic workflow: ship ladder M3 plus the user-scoped client, and have the agent's work checked

**Ticket:** combine `training/ladder/mid-03-lock-down-public-tables.md` with the first step of `senior-01`: move
`user_preferences` reads and writes (`backend/app/api/profile.py`) to a per-request user-scoped client. This is the
riskiest kind of change for AI assistants: it looks like a refactor but changes *who the database thinks is asking*.
Time: about 3 hours.

## 1. You write first (no agent yet), 30 min

- `spec.md` (½ page): the behaviour that must stay the same, the behaviour that changes (anon can't write listings;
  preferences are enforced by RLS), and what is out of scope.
- `design.md` (½ page):
  - where the per-request client is created and closed;
  - which operations stay on the service role and why;
  - the migration file and its order;
  - which tests prove isolation, **including under concurrency** (INC-004).

## 2. Implementer agent, 30–45 min

Prompt it with the spec, the design, and these constraints: "Don't touch files outside `backend/app/core/`,
`backend/app/api/profile.py`, `supabase/migrations/`. Don't modify tests in `training/`. Every claim in your summary must
name a test or a command output."

## 3. Adversarial reviewer (a different model if you can), 20 min

Give it the diff plus the spec. Its instructions: "Review only for correctness, security, isolation under concurrency,
failure handling, migration safety and test adequacy. No style comments. For every issue give file:line and a
failing-test idea. Explicitly check:
- (a) any module-level client or object that gets per-request state;
- (b) removed `user_id` filters;
- (c) RLS policies missing for any command the API now performs;
- (d) the maybe_single-returns-None trap;
- (e) whether the migration's rollout order breaks reads."

## 4. Revise, then verify yourself

Checklist (paste the outputs into the PR):
- [ ] `test_inc004_user_scoped_client.py`-style concurrency test for `/profile/preferences` passes (write it if the agent didn't)
- [ ] `test_inc003_api_contract.py` passes (no response-shape change)
- [ ] `test_junior01_first_time_user.py`: the preferences case passes
- [ ] RLS lab before/after: P5, P7, P8, P11 as expected, plus your own probe for preferences
- [ ] Read the whole diff. Every "RLS handles it" comment matches a policy that exists in SQL
- [ ] No placeholder or fake behaviour: no `pass`, no swallowed exceptions, no TODO-returns-True
- [ ] The migration is re-runnable (guards) and has a written rollback (`disable row level security` / `drop policy`)
- [ ] The agent's summary claims are each backed by an output you saw yourself

## 5. Your explanation (graded by the reviewer model)

In ≤300 words, answer three questions: how does the caller's identity reach Postgres now; what happens if a handler
forgets a filter; and what exactly would break if someone "optimized" the client into a singleton. Ask the reviewer to
grade it with `training/_answers/agentic/RUBRIC.md`.
