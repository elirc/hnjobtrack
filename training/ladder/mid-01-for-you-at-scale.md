# M1: For You takes 4 s once we keep 12 months of threads

**Context.** `GET /jobs/for-you` (`backend/app/api/jobs.py:76-122`):
1. Loads **every** listing of the latest thread (`select("*")` with no range, including `raw_text`).
2. Scores each one in Python (`services/match.py`), sorts them, and slices a page.
3. The handler is `async def` but calls the synchronous supabase client.

Product now wants For You to cover the last 3 threads (about 3,000 listings, ~2 KB `raw_text` each).

**Ticket.**
> For You must cover the last 3 months and stay under 400 ms p95 at 50 concurrent users. The match % shown must equal
> the drawer's breakdown (`get_match_breakdown`).

**Constraints.** Scoring rules stay as documented in `README.md` ("Match Scoring Algorithm"). Pagination must be stable:
no duplicates or gaps between pages when two jobs tie.

**Definition of done**
- A benchmark script (pytest-benchmark, or a timed loop with the fake DB and 3,000 generated rows) showing before/after.
- The design note names where scoring runs (Python, a SQL function, or precomputed) and why.
- `total` in the response is still correct.

**Explain before touching**
1. Measure first: of the 4 s, how much is transfer (row width), how much scoring, how much blocking the event loop? How will you tell?
2. What does `select("*")` pull that the list view never shows? (Compare with `JobCard.tsx`.)
3. Options: (a) project the columns + cache the scored list per user for N minutes; (b) move the scoring into a Postgres
   function (`skills && prefs.skills`, GIN index `idx_job_listings_skills`); (c) precompute scores when preferences or
   threads change. What invalidates each one?
4. Why does sorting by a float score need a tiebreaker for stable pages?

Answer: `training/_answers/ladder/mid-01.md`
