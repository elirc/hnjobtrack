# Reference placement: "Hide jobs I've dismissed"

1. **Data.** Use a new table, not a `saved_jobs.status` value. "Dismissed" and "saved" are independent (you can't be
   interviewing for a job you hid, and saved-status analytics shouldn't mix in dismissals).
   - `dismissed_jobs(user_id → auth.users on delete cascade, job_id → job_listings on delete cascade, dismissed_at
     timestamptz default now(), primary key(user_id, job_id))`.
   - RLS on, policies for select/insert/delete with `auth.uid() = user_id`; no update policy.
   - File `supabase/migrations/2026MMDD_dismissed_jobs.sql`, plus the same block in `schema.sql`, plus an RLS-lab probe
     that Ada can't see or delete Bob's dismissals.
2. **API** (new `backend/app/api/dismissed.py`, prefix `/jobs`, included before `jobs.router`, or under `/me/dismissed`
   to avoid the route-order trap from review R12):
   - `PUT /jobs/{id}/dismiss` → 204, idempotent via upsert on the primary key.
   - `DELETE /jobs/{id}/dismiss` → 204, idempotent.
   - `GET /me/dismissed` → a list.
   - Changes: `api/jobs.py` `list_jobs` switches to `get_optional_user`; `for_you_jobs`; `services/notifications.py`
     excludes per user.
3. **Query.** Filter in the database so `count` stays right: PostgREST `not.in.(ids)` when the dismissed list is small
   (fetch the user's ids first; cap at around 500), or better a view/RPC
   `jobs_for_user(uid)` = `job_listings` left anti-join `dismissed_jobs` that keeps exact counts. Anonymous users: no
   filter. For You filters before scoring. Digests: load each user's dismissed ids once per run.
4. **Frontend.**
   - `JobCard`/`JobDrawer` get a "Not interested" button with an `aria-label` naming the company.
   - Optimistic removal from the list state, with rollback on error.
   - The toast is a `role="status"` region with an Undo button. Focus moves to the next card, not lost; 5 s is too short
     for some users, so pause on hover/focus or make it dismissible only (WCAG 2.2.1).
   - A "Dismissed" tab in `app/saved/page.tsx`.
5. **Tests.**
   - API tests with the fake DB for each surface (list, for-you, digest builder) excluding a dismissed job.
   - Idempotency (double PUT, double DELETE).
   - The RLS lab probe for privacy.
   - The contract test updated for any new response models.
6. **Risk.** INC-004 (identity/isolation) if implemented with a shared user client, and INC-003 if response shapes
   change. Mitigation: explicit `user_id` filters plus RLS, the contract test, and no renames.
