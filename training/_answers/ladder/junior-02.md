# J2 answer

1. **Errors.** `.single()` with 0 rows makes postgrest-py raise `APIError` (PGRST116). Unhandled, FastAPI turns it into a
   500. A non-UUID id makes Postgres fail with `22P02 invalid input syntax for type uuid`, which PostgREST reports as 400,
   and that is also raised, so also a 500.
2. **Why type it `uuid.UUID`.** Validation happens at the edge: FastAPI returns 422 with a clear message, the DB never
   sees garbage, and the OpenAPI docs show the format. Catching DB errors mixes "bad input" with "DB down".
3. **Route order.** `main.py` includes `jobs.router` **before** `saved.router`, so `GET /jobs/saved/all` is checked
   against `/jobs/{job_id}` first. It only works because `/jobs/{job_id}` is a single segment and `saved/all` is two.
   `GET /jobs/saved` (one segment) *would* hit `get_job` with `job_id="saved"`. With `job_id: UUID` that becomes a 422;
   today it's a 500. The fix: declare static routes before parameterized ones, or give saved jobs their own prefix.

Reference: `job_id: UUID` on both handlers; then `rows = ...eq("id", str(job_id)).limit(1).execute().data`, and
`if not rows: raise HTTPException(404, "Job not found")`. Tests: the three cases × 2 endpoints, using the fake DB.
