-- ============================================
-- HN Jobs - Supabase Database Schema
-- Run this in the Supabase SQL Editor
-- ============================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ============================================
-- Profiles (extends Supabase auth.users)
-- ============================================
create type notify_frequency_enum as enum ('instant', 'daily', 'weekly');

create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  display_name text,
  notify_enabled boolean default false,
  notify_frequency notify_frequency_enum default 'weekly',
  created_at timestamptz default now()
);

alter table profiles enable row level security;

create policy "Users can view own profile"
  on profiles for select using (auth.uid() = id);

create policy "Users can update own profile"
  on profiles for update using (auth.uid() = id);

create policy "Users can insert own profile"
  on profiles for insert with check (auth.uid() = id);

-- Auto-create profile on signup
create or replace function handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();

-- ============================================
-- User Preferences
-- ============================================
create table user_preferences (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade unique,
  roles text[] default '{}',
  locations text[] default '{}',
  remote_only boolean default false,
  visa_sponsorship boolean default false,
  skills text[] default '{}',
  salary_min integer,
  excluded_companies text[] default '{}'
);

alter table user_preferences enable row level security;

create policy "Users can view own preferences"
  on user_preferences for select using (auth.uid() = user_id);

create policy "Users can update own preferences"
  on user_preferences for update using (auth.uid() = user_id);

create policy "Users can insert own preferences"
  on user_preferences for insert with check (auth.uid() = user_id);

-- ============================================
-- HN Threads
-- ============================================
create type thread_status_enum as enum ('pending', 'parsing', 'done', 'error');

create table hn_threads (
  id uuid primary key default uuid_generate_v4(),
  hn_post_id text not null unique,
  title text not null,
  month date not null,
  scraped_at timestamptz default now(),
  status thread_status_enum default 'pending'
);

-- ============================================
-- Job Listings
-- ============================================
create type remote_enum as enum ('yes', 'no', 'hybrid');
create type role_type_enum as enum ('full-time', 'part-time', 'contract', 'internship');

create table job_listings (
  id uuid primary key default uuid_generate_v4(),
  thread_id uuid not null references hn_threads(id) on delete cascade,
  hn_comment_id text not null,
  raw_text text,
  company text,
  role text,
  role_type role_type_enum,
  location text[] default '{}',
  remote remote_enum,
  visa_sponsorship boolean,
  salary_min integer,
  salary_max integer,
  salary_currency text,
  skills text[] default '{}',
  description text,
  apply_url text,
  apply_email text,
  equity boolean,
  parsed_at timestamptz,
  parse_confidence float,
  is_flagged boolean default false
);

create index idx_job_listings_thread on job_listings(thread_id);
create index idx_job_listings_company on job_listings(company);
create index idx_job_listings_skills on job_listings using gin(skills);
create index idx_job_listings_location on job_listings using gin(location);
create index idx_job_listings_remote on job_listings(remote);
create index idx_job_listings_parsed_at on job_listings(parsed_at desc);

-- Full text search index
alter table job_listings add column fts tsvector
  generated always as (
    to_tsvector('english',
      coalesce(company, '') || ' ' ||
      coalesce(role, '') || ' ' ||
      coalesce(description, '')
    )
  ) stored;

create index idx_job_listings_fts on job_listings using gin(fts);

-- ============================================
-- Saved Jobs
-- ============================================
create type saved_status_enum as enum ('saved', 'applied', 'interviewing', 'rejected', 'offer');

create table saved_jobs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  job_id uuid not null references job_listings(id) on delete cascade,
  saved_at timestamptz default now(),
  notes text,
  status saved_status_enum default 'saved',
  unique(user_id, job_id)
);

alter table saved_jobs enable row level security;

create policy "Users can view own saved jobs"
  on saved_jobs for select using (auth.uid() = user_id);

create policy "Users can insert own saved jobs"
  on saved_jobs for insert with check (auth.uid() = user_id);

create policy "Users can update own saved jobs"
  on saved_jobs for update using (auth.uid() = user_id);

create policy "Users can delete own saved jobs"
  on saved_jobs for delete using (auth.uid() = user_id);

create index idx_saved_jobs_user on saved_jobs(user_id);

-- ============================================
-- Notifications Log
-- ============================================
create table notifications_log (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  job_ids uuid[] default '{}',
  sent_at timestamptz default now(),
  email text not null
);

alter table notifications_log enable row level security;

create policy "Users can view own notifications"
  on notifications_log for select using (auth.uid() = user_id);
