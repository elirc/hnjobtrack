# HN Jobs

A full-stack job browser for Hacker News "Who's Hiring" threads. Scrapes threads monthly, parses every listing with GPT-4o-mini into structured data, and provides search, filtering, personalized match scoring, application tracking, and email notifications.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, APScheduler |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| **Database** | Supabase (PostgreSQL), Row Level Security, Full-Text Search |
| **Auth** | Supabase Auth (password + magic link), JWT verification |
| **AI** | OpenAI GPT-4o-mini (structured JSON output for job parsing) |
| **Email** | Resend API (digest notifications) |

## Features

- **AI-Parsed Listings** - GPT-4o-mini extracts company, role, salary, skills, location, remote status, visa sponsorship, equity, apply URL/email, and a confidence score from raw HN comments
- **Full-Text Search** - Search across companies, roles, skills, and descriptions with PostgreSQL `tsvector` indexing
- **Advanced Filters** - Filter by remote type (remote/hybrid/on-site), role type (full-time/part-time/contract/internship), skills, location, salary range, visa sponsorship
- **Personalized Match Scoring** - Set your preferences and get a 0-100 match score for every job with a detailed breakdown
- **Job Tracking** - Save jobs and track application status: Saved, Applied, Interviewing, Rejected, Offer. Add personal notes to each
- **Email Digests** - Instant, daily, or weekly email notifications with your top-matched jobs from the latest thread
- **Auto Scraping** - Scheduled monthly scrape on the 1st of each month via APScheduler, with admin API for manual triggers
- **Responsive UI** - Mobile-first design with collapsible filter sidebar, job detail drawer, and accessible components

## Architecture

```
HNJOBTRACK/
├── backend/                   Python FastAPI application
│   └── app/
│       ├── main.py              App entry point, CORS, scheduled jobs
│       ├── core/
│       │   ├── config.py          Pydantic settings (env vars)
│       │   ├── supabase.py        Supabase client init (admin + public)
│       │   └── auth.py            JWT auth middleware (get_current_user, require_admin)
│       ├── api/
│       │   ├── jobs.py            Job listing endpoints (list, filter, for-you, match)
│       │   ├── saved.py           Saved jobs endpoints (save, update, unsave, list)
│       │   ├── profile.py         Profile & preferences endpoints
│       │   └── admin.py           Admin endpoints (trigger scrape, status, notify)
│       ├── services/
│       │   ├── scraper.py         HN Algolia API scraper (threads + comments)
│       │   ├── parser.py          GPT-4o-mini job parser (raw text -> structured JSON)
│       │   ├── match.py           Match scoring algorithm (0-100, 6 factors)
│       │   └── notifications.py   Email digest generation via Resend
│       └── schemas/
│           ├── jobs.py            Job listing Pydantic models
│           ├── saved.py           Saved job Pydantic models
│           └── profile.py         Profile/preferences Pydantic models
│
├── frontend/                  Next.js 14 application
│   └── src/
│       ├── app/
│       │   ├── page.tsx           Landing page (hero, features, how-it-works, CTA)
│       │   ├── layout.tsx         Root layout with Navbar
│       │   ├── auth/
│       │   │   ├── login/page.tsx   Login (password + magic link)
│       │   │   ├── signup/page.tsx  Signup with email confirmation
│       │   │   └── callback/route.ts  Auth callback handler
│       │   ├── dashboard/
│       │   │   ├── page.tsx         Job browse with search, filters, sort, pagination
│       │   │   ├── layout.tsx       Dashboard Suspense wrapper
│       │   │   └── for-you/page.tsx Personalized matches page
│       │   ├── profile/page.tsx     Profile & preferences editor
│       │   └── saved/page.tsx       Saved jobs with status tracking & notes
│       ├── components/
│       │   ├── Navbar.tsx           Navigation with auth state
│       │   ├── JobCard.tsx          Job listing card with save, salary, skills
│       │   ├── JobDrawer.tsx        Job detail drawer with match breakdown
│       │   ├── FilterSidebar.tsx    Collapsible filter panel (mobile + desktop)
│       │   ├── SkillBadge.tsx       Color-coded skill tags (18 tech colors)
│       │   └── MatchScoreBar.tsx    Visual match score indicator
│       ├── lib/
│       │   ├── supabase.ts         Browser Supabase client
│       │   └── api.ts              API client (fetch jobs, save, profile, prefs)
│       ├── types/index.ts          TypeScript interfaces
│       └── middleware.ts            Route protection (profile, saved, for-you)
│
├── supabase/
│   └── schema.sql               Complete DB schema (6 tables, RLS, indexes, triggers)
│
├── .env.example                 Backend env vars template
└── .gitignore
```

## Database Schema

| Table | Purpose |
|-------|---------|
| `profiles` | User profiles (extends Supabase auth.users). Auto-created via trigger on signup |
| `user_preferences` | Job match preferences (roles, skills, locations, salary, remote, visa, excluded companies) |
| `hn_threads` | Scraped HN "Who's Hiring" threads (title, month, status) |
| `job_listings` | Parsed job listings with 15+ structured fields, full-text search index, GIN indexes on skills/location |
| `saved_jobs` | User's saved jobs with status tracking (saved/applied/interviewing/rejected/offer) and notes |
| `notifications_log` | Email notification audit log |

All user-facing tables have Row Level Security policies. The `job_listings` table has GIN indexes on `skills` and `location` arrays, plus a generated `tsvector` column for full-text search.

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) account (free tier works)
- An [OpenAI](https://platform.openai.com) API key (GPT-4o-mini)
- A [Resend](https://resend.com) API key (for email notifications, optional)

### 1. Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the entire contents of `supabase/schema.sql`
   - This creates all tables, enums, indexes, RLS policies, and the auto-profile trigger
3. Go to **Settings > API** and note:
   - Project URL (`SUPABASE_URL`)
   - `anon` public key (`SUPABASE_ANON_KEY`)
   - `service_role` secret key (`SUPABASE_SERVICE_ROLE_KEY`)
4. Go to **Settings > Database** and note the connection string (`DATABASE_URL`)

### 2. Backend

```bash
cd backend
python -m venv venv

# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

Create `backend/.env` from the template:

```bash
cp ../.env.example .env
```

Fill in your values:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
OPENAI_API_KEY=sk-your-key
RESEND_API_KEY=re_your-key
FROM_EMAIL=jobs@yourdomain.com
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ADMIN_API_KEY=your-secret-admin-key
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/health` should return `{"status":"ok"}`

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local` from the template:

```bash
cp .env.local.example .env.local
```

Fill in your values:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 4. Initial Data Load

With both servers running, trigger the first scrape:

```bash
curl -X POST http://localhost:8000/admin/scrape \
  -H "X-Api-Key: your-secret-admin-key"
```

This runs in the background and will:
1. Fetch the latest "Who's Hiring" thread from HN Algolia API
2. Extract all top-level comments (job posts)
3. Parse each comment through GPT-4o-mini into structured data
4. Store everything in Supabase

Check progress:

```bash
curl http://localhost:8000/admin/status \
  -H "X-Api-Key: your-secret-admin-key"
```

### 5. Production Build

```bash
cd frontend
npm run build
npm start
```

## API Reference

### Jobs

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/jobs` | Optional | List jobs with search, filters, sorting, pagination |
| `GET` | `/jobs/for-you` | Required | Jobs scored and sorted by user preferences |
| `GET` | `/jobs/{id}` | None | Get a single job listing |
| `GET` | `/jobs/{id}/match` | Required | Detailed match score breakdown for a job |

**Query params for `GET /jobs`:**
- `search` - Full-text search (company, role, description, skills)
- `remote` - `yes`, `no`, or `hybrid`
- `role_type` - `full-time`, `part-time`, `contract`, or `internship`
- `skills` - Comma-separated skill names
- `location` - Location filter
- `visa_sponsorship` - `true`/`false`
- `salary_min` / `salary_max` - Salary range filter
- `sort_by` - `recent` (default) or `salary_desc`
- `page` / `per_page` - Pagination (default: page 1, 20 per page)
- `thread_id` - Filter to specific HN thread

### Saved Jobs

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/jobs/{id}/save` | Required | Save a job (body: `{notes?, status?}`) |
| `PUT` | `/jobs/{id}/save` | Required | Update saved job (body: `{status?, notes?}`) |
| `DELETE` | `/jobs/{id}/save` | Required | Remove a saved job |
| `GET` | `/jobs/saved/all` | Required | List all saved jobs (query: `?status=applied`) |

**Saved statuses:** `saved`, `applied`, `interviewing`, `rejected`, `offer`

### Profile & Preferences

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/profile` | Required | Get user profile |
| `PUT` | `/profile` | Required | Update display name, notification settings |
| `GET` | `/profile/preferences` | Required | Get job match preferences |
| `PUT` | `/profile/preferences` | Required | Update match preferences |

### Admin

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/admin/scrape` | Admin (`X-Api-Key` header) | Trigger scrape + parse pipeline |
| `GET` | `/admin/status` | Admin | View thread stats (total, parsed, flagged) |
| `POST` | `/admin/notify` | Admin | Trigger email digest notifications |
| `GET` | `/health` | None | Health check |

## Match Scoring Algorithm

Jobs are scored 0-100 based on user preferences:

| Factor | Max Points | Logic |
|--------|-----------|-------|
| Skill overlap | 40 | `(matching_skills / min(user_skills, job_skills)) * 40` |
| Role match | 20 | Full match = 20 pts, partial word match (50%+) = 10 pts |
| Location match | 15 | Substring match between user and job locations |
| Remote preference | 10 | Remote-only user + remote/hybrid job = 10, non-remote-only = 5 |
| Salary fit | 10 | Job salary_max >= user salary_min = 10, within 80% = 5 |
| Visa sponsorship | 5 | User needs visa + job offers = 5, user doesn't need = 5 |

Companies in the user's excluded list automatically get a score of **0**.

## Scheduled Jobs

The backend runs three scheduled jobs via APScheduler:

| Job | Schedule | Action |
|-----|----------|--------|
| Monthly scrape | 1st of month, 12:00 UTC | Scrape latest thread, parse all jobs, send instant notifications |
| Daily digest | Every day, 09:00 UTC | Send daily digest emails to subscribed users |
| Weekly digest | Every Monday, 09:00 UTC | Send weekly digest emails to subscribed users |

## Email Notifications

Users can opt into email digests at three frequencies:
- **Instant** - Sent immediately after a new thread is scraped and parsed
- **Daily** - Sent at 9am UTC with jobs parsed in the last 24 hours
- **Weekly** - Sent Monday at 9am UTC with jobs parsed in the last 7 days

Each email contains up to 10 top-matched jobs (score > 20) with company, role, location, salary, skills, and match percentage. Includes links to view all matches and manage preferences/unsubscribe.

## GPT-4o-mini Parsing

Each raw HN comment is sent to GPT-4o-mini with a structured JSON schema prompt. The model extracts:

| Field | Type | Description |
|-------|------|-------------|
| `company` | string | Company name |
| `role` | string | Job title |
| `role_type` | enum | full-time, part-time, contract, internship |
| `location` | string[] | Array of locations (city + state/country) |
| `remote` | enum | yes, no, hybrid |
| `visa_sponsorship` | boolean | Whether visa is offered |
| `salary_min` / `salary_max` | integer | Annual salary range (normalized to USD) |
| `salary_currency` | string | Currency code |
| `skills` | string[] | Technologies, languages, frameworks |
| `description` | string | Cleaned job summary |
| `apply_url` | string | Application URL |
| `apply_email` | string | Application email |
| `equity` | boolean | Whether equity is offered |
| `parse_confidence` | float | 0.0-1.0 confidence score |

Comments are processed in batches of 20 concurrent requests with `temperature=0.1` for consistent output.
