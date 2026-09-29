-- Apply separately to an existing database. It intentionally fails if
-- duplicate logical comments already exist; review and reconcile those rows
-- rather than silently deleting parsed or user-visible data.
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'job_listings'::regclass
      and conname = 'job_listings_thread_comment_unique'
  ) then
    alter table job_listings
      add constraint job_listings_thread_comment_unique
      unique(thread_id, hn_comment_id);
  end if;
end $$;
