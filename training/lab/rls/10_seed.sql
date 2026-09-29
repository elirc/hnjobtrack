-- Two users, one thread, two listings, one saved job + preferences each.
-- Run as the superuser (the "service role" of this lab).
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'ada@example.com'),
  ('22222222-2222-2222-2222-222222222222', 'bob@example.com');
-- handle_new_user() has created both profiles rows via the trigger in schema.sql.

insert into hn_threads (id, hn_post_id, title, month, status) values
  ('aaaaaaaa-0000-0000-0000-000000000001', '42000000', 'Ask HN: Who is hiring? (September 2026)', '2026-09-01', 'done');

insert into job_listings (id, thread_id, hn_comment_id, raw_text, company, role, role_type, remote, skills, parsed_at) values
  ('bbbbbbbb-0000-0000-0000-000000000001', 'aaaaaaaa-0000-0000-0000-000000000001', '42000101',
   'Acme | Backend Engineer | Remote (US) | Python, Postgres', 'Acme', 'Backend Engineer', 'full-time', 'yes', '{python,postgres}', now()),
  ('bbbbbbbb-0000-0000-0000-000000000002', 'aaaaaaaa-0000-0000-0000-000000000001', '42000102',
   'Globex | Frontend Engineer | NYC | React, TypeScript', 'Globex', 'Frontend Engineer', 'full-time', 'no', '{react,typescript}', now());

insert into saved_jobs (user_id, job_id, status, notes) values
  ('11111111-1111-1111-1111-111111111111', 'bbbbbbbb-0000-0000-0000-000000000001', 'saved', 'ada: referral from Sam'),
  ('22222222-2222-2222-2222-222222222222', 'bbbbbbbb-0000-0000-0000-000000000002', 'applied', 'bob: salary band 180k');

insert into user_preferences (user_id, skills, roles) values
  ('11111111-1111-1111-1111-111111111111', '{python}', '{backend engineer}'),
  ('22222222-2222-2222-2222-222222222222', '{react}', '{frontend engineer}');
