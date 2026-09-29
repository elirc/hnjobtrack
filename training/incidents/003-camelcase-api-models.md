# INC-003: Salaries vanished and users get jobs from companies they excluded

**Branch:** `training/incidents/003-camelcase-api-models` · **Severity:** SEV-2 · **Time box:** 40 min

## What on-call sees

A backend-only deploy went out Tuesday 14:00. The frontend was not redeployed. No backend errors, 5xx rate flat at 0.02%.

Support tickets, Tuesday to Thursday:

- "Salary ranges disappeared from every job card." (×9)
- "The match % bar is gone on For You."
- "My profile page shows my name blank and notifications unchecked, but I'm still getting emails?"
- "I excluded Initech months ago and today's digest is full of Initech jobs." (×4, all Wednesday or later)

Browser error tracker (new since Tuesday 14:05):

```
Failed to load profile: TypeError: Cannot read properties of undefined (reading 'join')
    at loadData (app/profile/page.tsx)          1,240 events · 611 users
```

Data team query, run Thursday:

```sql
select date_trunc('day', now()) as asof,
       count(*) filter (where excluded_companies = '{}')::float / count(*) as share_empty
from user_preferences;
-- Monday: 0.41   Thursday: 0.69
```

The HN link button in the job drawer now opens `https://news.ycombinator.com/item?id=undefined`.

## Suspect change

`775891c refactor(api): camelCase JSON for all API models`. The PR description says: "populate_by_name keeps snake_case
request bodies working, so existing callers are unaffected." The reviewer approved: "clean, no endpoint changes."

## Your job

1. Explain every symptom above, including why the damage **grew** on Wednesday although nothing new was deployed.
   Trace it through `frontend/src/app/profile/page.tsx` (`loadData`, `handleSave`) and `frontend/src/lib/api.ts`.
2. Say why no backend test or type check caught it, and which test would have.
3. Roll back or roll forward? Decide, and say what you do about the preferences rows that were already overwritten.
4. Design the way to ship camelCase for the mobile client without breaking the web client.

Sealed answer: `training/_answers/incidents/003-camelcase-api-models.md`
