-- Minimal stand-in for the parts of Supabase that supabase/schema.sql depends on.
-- It is NOT Supabase. It reproduces exactly three things that matter for RLS:
--   1. the anon / authenticated / service_role roles (service_role has BYPASSRLS, like on Supabase)
--   2. auth.users + auth.uid(), where auth.uid() reads the JWT "sub" claim the way PostgREST exposes it
--      (PostgREST sets request.jwt.claims per request after it has VERIFIED the JWT signature)
--   3. Supabase's default grants: every table in public is fully granted to anon and authenticated,
--      so RLS is the only thing standing between the anon key and your data.
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then create role service_role nologin bypassrls; end if;
end $$;

create schema auth;
create table auth.users (id uuid primary key, email text);

create function auth.uid() returns uuid
language sql stable as $$
  select nullif(nullif(current_setting('request.jwt.claims', true), '')::json ->> 'sub', '')::uuid
$$;

grant usage on schema public, auth to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
alter default privileges in schema public grant all on functions to anon, authenticated, service_role;
