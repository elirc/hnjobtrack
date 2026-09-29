# M1 answer: For You at scale

1. **Measure before choosing.** Time three things separately:
   - (a) the PostgREST response: bytes and ms for `select("*")` of 3,000 rows, where `raw_text` plus `description` dominate
     at around 6+ MB;
   - (b) the `compute_match_score` loop (3,000 small dicts: a few ms);
   - (c) event-loop blocking, since the sync client inside `async def` blocks other requests for the whole transfer.

   Expect (a) and (c) to dominate. Scoring in Python is not the problem.
2. **Unused columns.** The list view (`JobCard.tsx`) never shows `raw_text`, `description`, `apply_email` or
   `parse_confidence`. Project only the columns the card and the scorer need: `id, thread_id, hn_comment_id, company,
   role, role_type, location, remote, visa_sponsorship, salary_*, skills, equity, parsed_at`.
3. **Options and their invalidation.**
   - (a) Cache the scored list per user for a few minutes. Invalidate on a preferences change or a new thread. Simple,
     but the first hit stays slow and memory grows with users.
   - (b) Score in SQL, as a Postgres function taking the preferences and returning `(id, score)` ordered by score.
     Nothing to invalidate and one round trip. The cost: scoring logic duplicated in SQL (drift risk against
     `get_match_breakdown`, so add a parity test with ~50 generated jobs).
   - (c) Precompute a `user_job_scores` table. Invalidate on a preferences change (rescore that user) or a new thread
     (rescore all users: a batch job). Fastest reads; the most moving parts.

   Reference choice at this scale: **projection + a threadpool call + a short cache (a)**, and (b) only if p95 is still
   over budget. Say which one you'd pick and why.
4. **Stable pages.** Many jobs share a score (the scores are discrete sums), and Python's sort is stable only relative to
   input order, which PostgREST doesn't guarantee without an ORDER BY. So add `ORDER BY parsed_at desc, id` before
   scoring, or sort by `(-score, id)`.

Grading: numbers before a decision; noticing the loop blocking; the parity test between the two scoring implementations.
