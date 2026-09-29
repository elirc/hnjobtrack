# Rubric for the agentic exercise (reviewer model: use this verbatim)

Score 0–2 per row (10 max). Quote the learner's words as evidence for each score.

| # | Criterion | 2 = | 0 = |
|---|---|---|---|
| 1 | Identity path | Names the exact path: Bearer token → per-request PostgREST client headers → PostgREST verifies it → `auth.uid()` in the policy | "RLS knows the user" |
| 2 | Defense in depth | Explains that the explicit filter AND RLS both remain; says what each one catches | Says RLS makes filters redundant |
| 3 | Singleton hazard | Explains that shared mutable headers plus concurrency send the wrong identity, and that RLS then "correctly" serves the wrong user's rows | Doesn't know, or says "thread-safety issue" with no mechanism |
| 4 | Verification | Cites the concurrency test and the lab probe outputs they actually ran | Cites only "tests pass" |
| 5 | Scope honesty | States what stayed on the service role and why, plus one remaining risk | Claims everything is now safe |

Things the reviewer model should have caught in a typical agent diff (check that the learner handled them):
- a client cached at module level "for performance"
- `.eq("user_id", ...)` removed
- no delete policy on `user_preferences`
- a migration that enables RLS before creating the SELECT policy on `job_listings`
