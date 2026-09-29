-- Reference migration for ladder/mid-03 (sealed). Apply AFTER supabase/schema.sql.
-- job_listings and hn_threads are written only by the backend (service role, which bypasses RLS);
-- everyone may read them. So: enable RLS, add a read policy, add NO write policy.
alter table hn_threads   enable row level security;
alter table job_listings enable row level security;

create policy "Listings are public" on job_listings for select to anon, authenticated using (true);
create policy "Threads are public"  on hn_threads   for select to anon, authenticated using (true);

-- Belt and braces: the anon/authenticated roles never need to write these tables at all.
revoke insert, update, delete, truncate on job_listings, hn_threads from anon, authenticated;

-- Functional gap found by probe P5: users can create/update preferences but never delete them.
create policy "Users can delete own preferences"
  on user_preferences for delete using (auth.uid() = user_id);
