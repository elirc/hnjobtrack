# Blind review: HN Jobs (60 minutes)

You're the new senior engineer. Before your first feature, the lead asks for a written review of `main`.

**Scope:** `backend/app/**`, `backend/tests/**`, `supabase/schema.sql`, `supabase/migrations/**`,
`frontend/src/**`, `README.md`. Skip `astraupskill/` (an older learning pack).

**Rules**
- 60 minutes, timer on. No AI assistance for the first pass. Afterwards you may ask an agent for a second pass, but
  record which findings came from it (see `training/agentic/`).
- For each finding write: **severity** (critical/high/medium/low) · **file:line** · **what goes wrong in production, for
  whom** · **how you'd prove it** (a test, a lab probe, a log query) · **fix sketch** in one line.
- Mark the findings you think are typical of AI-generated code (e.g. tests that only confirm the author's assumption, docs
  claiming features the code doesn't have, fail-open defaults).
- Rank by production severity, not by how easy the fix is.

**Areas to be sure you covered.** Isn't a hint list, just coverage:
correctness · authn/authz · database-enforced isolation (what does Postgres itself stop?) · data integrity · async/await
correctness in Python · failure handling of background jobs · LLM output handling · performance · operability · tests ·
accessibility · docs vs reality.

**Tools you may use:** `training/lab/rls/rls_lab.py` (what the anon/authenticated/service roles can really do),
`training/lab/fake_supabase.py` + FastAPI `TestClient` for quick experiments. See `training/lab/README.md`.

When done, open `training/review/COMPARE.md`, then the sealed model review `training/_answers/review.md`.
