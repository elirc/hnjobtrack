# INC-005: December's thread is stuck at 21% parsed

**Branch:** `training/incidents/005-multi-role-type-prompt` · **Severity:** SEV-3 (degraded product, no data loss) · **Time box:** 40 min

## What on-call sees

December 3, a user writes: "The December listings look thin. Half the companies I saw on HN aren't in HN Jobs."

`GET /admin/status` (`backend/app/api/admin.py`):

```json
{"threads": {
  "Ask HN: Who is hiring? (December 2026)": {"status": "parsing", "total_comments": 1012, "parsed": 214, "flagged": 0, "scraped_at": "2026-12-01T12:00:04Z"},
  "Ask HN: Who is hiring? (November 2026)": {"status": "done", "total_comments": 987, "parsed": 961, "flagged": 26, "scraped_at": "2026-11-01T12:00:03Z"}
}}
```

A manual `POST /admin/scrape` on Dec 3 returns `{"status": "scrape started"}`. Ten minutes later: still `parsed: 214`.
A second attempt an hour later: `parsed: 229`. A third: `parsed: 229`.

The only log lines from Dec 1 12:00–13:00 at WARNING or above:

```
12:03:17 ERROR apscheduler.executors.default Job "monthly_scrape_job (trigger: cron[day='1', hour='12', minute='0'], next run at: 2027-01-01 12:00:00 UTC)" raised an exception
Traceback (most recent call last):
  ...
  File "backend/app/services/parser.py", line 89, in parse_thread_jobs
    sb.table("job_listings").update(update_data).eq("id", job["id"]).execute()
  ...
postgrest.exceptions.APIError: {'code': '22P02', 'details': None, 'hint': None, 'message': 'invalid input value for enum role_type_enum: "full-time, contract"'}
```

No alert fired. Instant-digest users got no December email.

## Suspect change (deployed Nov 20)

`15acb62 feat(parser): capture multi-role posts`: "Prompt-only change; no schema or code changes."

## Your job

1. Explain why 214 rows were parsed (not 0 and not 1,012), why re-runs add nothing or almost nothing, and why the
   second re-run did add 15.
2. Decide: is the bug in the prompt PR or in code that was already on main? Prove it with a test that uses recorded
   model output (no API calls; there are fixtures in `training/lab/fixtures/`).
3. Name every place a model answer crosses into the database or the UI without validation.
4. Fix the pipeline so one bad answer can't stall a thread. Decide what happens to multi-type posts.
5. Say which alert would have caught this on Dec 1, and what the eval for prompt changes should look like.

Sealed answer: `training/_answers/incidents/005-multi-role-type-prompt.md`
