# J2: `GET /jobs/{id}` returns 500 for a job that doesn't exist

**Context.** `backend/app/api/jobs.py:125-129` (`get_job`) and `:132-135` (`get_job_match`) use `.single().execute()`.
Listings are deleted when a thread is removed (`job_listings.thread_id ... on delete cascade`, `supabase/schema.sql:96`),
so old shared links and saved bookmarks point at missing ids. Ids are UUIDs, and anyone can type anything into the URL.

**Ticket.**
> Old links from last month's digest email show a blank drawer and our error tracker logs a 500. Missing jobs should be a
> clean 404, and garbage ids should be a 422, not a database error.

**Constraints.** No new dependencies. The frontend expects `{"detail": "..."}` on errors (`frontend/src/lib/api.ts:40`).

**Definition of done**
- `GET /jobs/<valid-uuid-not-in-db>` → 404, `GET /jobs/not-a-uuid` → 422, and the same for `/jobs/{id}/match`.
- Tests with FastAPI's `TestClient` plus `training/lab/fake_supabase.py` (see `training/lab/README.md`) for all three cases.

**Explain before touching**
1. What does `.single()` raise when there are 0 rows? What would Postgres say about `id = 'not-a-uuid'`?
2. Why is typing the path parameter as `uuid.UUID` better than catching the DB error?
3. `/jobs/saved/all` sits in `api/saved.py`, but it's matched against the `/jobs/{job_id}` route in `api/jobs.py`.
   Why does it still work? Check the router include order in `main.py:61-64`. What would break if the path parameter
   were typed `UUID` and the include order changed?

Answer: `training/_answers/ladder/junior-02.md`
