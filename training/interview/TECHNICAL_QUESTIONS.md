# 20 technical questions about HN Jobs

Answer out loud, then check `training/_answers/interview/TECHNICAL_ANSWERS.md`.

## API design
1. `saved.py` uses the `/jobs` prefix, the same as `jobs.py`. What breaks if someone adds `GET /jobs/saved`, and how would you restructure the routes?
2. `POST /jobs/{id}/save` does a lookup, then an insert. What does a double click return today, and what should it return?
3. `/jobs` returns `raw_text` in list responses. Why is that a problem, and how do you remove it without breaking the frontend?
4. How would you version the API so the mobile client gets camelCase (INC-003) without hurting the web client?

## Database
5. What does the `unique(thread_id, hn_comment_id)` constraint buy the scraper, and why is the migration written as a guarded `do $$` block?
6. The `fts` generated column exists but no query uses it. How do you prove an index is used, and what changes for users if search moves to it?
7. `saved_jobs.job_id` cascades on delete from `job_listings`, which cascades from `hn_threads`. What user-visible bug follows from deleting an old thread?
8. With RLS enabled and no DELETE policy on `user_preferences`, what does a delete by the owner do? Why is that worse than an error?

## Auth and multi-tenancy
9. The backend uses the service-role key. Draw the path of a request and mark where isolation is actually enforced.
10. Why can't RLS policies protect data from a bug in `get_current_user`?
11. If you moved to a per-request user client, which operations must stay on the service role?
12. For a Teams plan, compare a JWT org claim with a membership lookup in the policy. What happens when a member is removed?

## Python / async
13. What happens to other requests while a sync supabase-py call runs inside an `async def` handler? And inside a plain `def` handler?
14. Why did `time.sleep` in the parser take down `/health`, and how would you detect it in production?

## AI features
15. Where does model output enter the system without validation, and what's the worst outcome at each point?
16. How would you gate prompt changes before they reach the monthly run?

## Testing
17. The repo's scraper tests pass although the code crashes on the first scrape of a month. What's the general lesson about fakes?
18. What does a consumer-driven contract test between this FastAPI app and `frontend/src/types/index.ts` look like?

## Operations
19. Two uvicorn workers are started. What happens to the cron jobs, and how do you fix it?
20. A manual `/admin/scrape` re-run emails every instant-digest user again. Design the dedupe.
