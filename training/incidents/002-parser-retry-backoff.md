# INC-002: The whole API goes dark at noon on the 1st

**Branch:** `training/incidents/002-parser-retry-backoff` · **Severity:** SEV-2 · **Time box:** 45 min

## What on-call sees

October 1, the monthly scrape (`monthly_scrape_job` in `backend/app/main.py`, cron day=1 12:00 UTC) starts on schedule.

```
12:00:02  uptime-check  GET /health  200  4ms
12:00:41  uptime-check  GET /health  TIMEOUT (10s)
12:01:41  uptime-check  GET /health  TIMEOUT (10s)
   ... 29 more timeouts ...
12:33:12  uptime-check  GET /health  200  9ms
```

| metric (12:00–12:35 UTC) | normal | during the window |
|---|---|---|
| `/jobs` p95 | 140 ms | 27.9 s |
| `/health` success rate | 100% | 6% |
| process CPU | 5–10% | **4–7%** |
| memory | 180 MB | 190 MB |
| OpenAI requests/min | ~0 | ~300, then 429s |

Application log excerpt (one uvicorn worker, `uvicorn app.main:app`):

```
12:00:39 WARNING app.services.parser parse retry job=5b1e… attempt=1 delay=1s err=RateLimitError
12:00:40 WARNING app.services.parser parse retry job=9c02… attempt=1 delay=1s err=RateLimitError
12:00:41 WARNING app.services.parser parse retry job=0f7d… attempt=1 delay=1s err=RateLimitError
12:00:45 WARNING app.services.parser parse retry job=5b1e… attempt=2 delay=2s err=RateLimitError
   ... 1,900 similar lines ...
12:32:58 INFO     thread 3f9a… status=done  parsed=1011 flagged=3
```

Parsing itself ended well: only 3 flagged listings, against 31% flagged in September. The team calls the retry PR a success.

## Suspect change (deployed Sep 26)

`da7b07d fix(parser): retry OpenAI 429s and timeouts with exponential backoff` (`backend/app/services/parser.py`).

## Your job

1. Explain why `/health` (which touches nothing but a dict) timed out while CPU stayed low.
2. Reproduce it deterministically without calling OpenAI (hint-free: you choose the tool).
3. Say which of the four retryable exception types should **not** be retried, and why.
4. Fix it, add a regression test, and name the second, independent problem the fix does not solve
   (`README.md` says "batches of 20 concurrent requests").
5. Postmortem.

Sealed answer: `training/_answers/incidents/002-parser-retry-backoff.md`
