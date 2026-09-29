# S2: Take the scrape → parse → notify pipeline out of the API process

**Context.** `backend/app/main.py:33-43` starts an `AsyncIOScheduler` inside the web process. It runs the monthly
scrape, the parse (about 1,000 OpenAI calls) and three digest schedules. `POST /admin/scrape` runs the same pipeline via
`BackgroundTasks`. Consequences so far:
- INC-002: the pipeline froze the API.
- INC-005: a failure stalled a thread silently.
- `api/admin.py:21` calls `send_digest_notifications()` with the default `frequency="instant"`, so each manual re-scrape
  emails every instant-digest user again. There is no dedupe, even though `notifications_log` exists.
- With 2 uvicorn workers or 2 instances, every cron job runs twice.

**Scenario.** Design the replacement so the product can go to 2+ API instances, and so that a re-run never double-emails.

**Operating constraints**
- Keep Supabase Postgres; no new paid service over $20/month. A Postgres-backed queue is acceptable.
- OpenAI budget of $15/month for parsing, with a hard stop.
- A thread must be resumable: re-running processes only what's missing.
- Every stage is observable: parsed %, flagged %, cost, digest sent/failed per frequency.

**Deliverables**
1. The component diagram, and where scheduling lives (exactly one scheduler: why and how?).
2. The job model and state machine for a thread and for each listing (reuse `hn_threads.status`, or add a table?).
3. Retry policy per failure class (429, timeout, invalid output, DB error), and where poison items go.
4. Digest idempotency: the key, the table, and what happens if the email provider accepts the send but the log insert fails
   (see `curriculum/01-transactional-outbox.md` and `curriculum/02-idempotency.md`; link, don't re-derive).
5. Cost control: token estimation before the call, the monthly budget counter, and when to use the Batch API.
6. Rollout: how to run the old and new pipelines side by side for one month without double work.

**Explain before touching:** list the three decisions you'd want a second reviewer to challenge.

Rubric: `training/_answers/ladder/senior-02.md`
