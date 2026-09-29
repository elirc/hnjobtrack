# M3: What can the public anon key do to our data?

**Context.** The browser ships `NEXT_PUBLIC_SUPABASE_ANON_KEY` (`frontend/.env.local.example`,
`frontend/src/lib/supabase.ts`), so treat it as public. Supabase grants table privileges in `public` to `anon` and
`authenticated` by default, and **RLS is the only gate**. `supabase/schema.sql` enables RLS on `profiles`,
`user_preferences`, `saved_jobs` and `notifications_log`, but not on `hn_threads` or `job_listings`.

**Ticket.**
> Security review item: prove what the anon key can and cannot do against our schema, and close whatever it shouldn't be
> able to do. Listings must stay publicly readable.

**Constraints**
- Deliver it as a migration file under `supabase/migrations/`, safe to run on the live project.
- The backend (service role) must keep working unchanged.

**Definition of done**
- The RLS lab (`training/lab/rls/rls_lab.py`, see `training/lab/README.md`) run **before** and **after** your migration,
  both outputs pasted into the PR. P7 and P8 must be denied, and P11 (anon reads listings) must still work.
- A probe you add yourself for a case the lab doesn't cover yet.

**Explain before touching**
1. Run the lab on main first. Which probe results surprise you, and what is the real-world impact of each?
2. RLS enabled with **no** policy for a command: what happens to that command? Is that enough, or do you also revoke grants? Why both?
3. Why does the service role keep working without any policy?
4. What must the rollout order be if the frontend ever reads `job_listings` directly with the anon key?

Answer (reference migration + reasoning): `training/_answers/ladder/mid-03.md`
