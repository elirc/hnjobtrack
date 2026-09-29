# INC-003 answer: an unchecked wire-format change, then data loss through the UI

## Symptom

After a backend-only deploy: salaries and match bars disappeared, the profile page threw
`Cannot read properties of undefined (reading 'join')`, HN links pointed to `id=undefined`, and from Wednesday on, users
received jobs from companies they had excluded. The share of empty `excluded_companies` rows rose from 41% to 69%.

## Diagnostic path

1. The frontend wasn't redeployed, so compare the **actual JSON** the API returned before and after, not the Python code.
   `curl /jobs` shows `salaryMin`, `perPage`, `hnCommentId`.
2. Check which fields survived: single-word keys (`id`, `company`, `skills`, `location`) look identical in both cases,
   which is why the UI only half broke.
3. Follow the profile page: `frontend/src/app/profile/page.tsx` `loadData()` fills state field by field, then throws at
   `prefsData.excluded_companies.join`. The error is swallowed by `catch → console.error`, so the form renders
   half-populated.
4. Explain the growth: `handleSave()` sends `excluded_companies: splitTrim("") = []`. The snake_case write is still
   accepted, so each save overwrote real exclusions with `[]`. `notify_enabled: undefined` is dropped by
   `JSON.stringify`, which is why emails kept coming.

## Root cause

- `backend/app/schemas/base.py:13` (branch): `ConfigDict(alias_generator=to_camel, populate_by_name=True)` applied to every
  schema. FastAPI serializes `response_model` **by alias**, so every multi-word response key changed.
  `populate_by_name` only affects input, so "existing callers unaffected" was true for requests and false for responses.
- The missing check: no contract test between the API and `frontend/src/types/index.ts`, and `apiFetch<T>`
  (`frontend/src/lib/api.ts`) casts the JSON instead of validating it.

## Fix

Roll back: revert `775891c`. No consumer depends on camelCase yet, so the revert is safe and immediate. Rolling forward
would leave the data loss running while the web client is changed.

**Repair the data:**
1. Restore a pre-Tuesday backup (PITR) into a side database.
2. For preferences whose `excluded_companies` went from non-empty to `{}` after Tuesday 14:00, restore that column only,
   and only where the user didn't deliberately change it since.
3. Tell the affected users.
4. Add `updated_at` and an audit trail so the next repair doesn't need a restore.

**Shipping camelCase later:** pick one of these, and add the contract test first.
- Don't: the mobile client can map keys itself.
- Use a versioned surface for the new format.
- Expand/contract: emit both key styles for a while, migrate the web client, then remove snake_case once telemetry shows
  no readers.

## Regression test

`training/_answers/regression-tests/test_inc003_api_contract.py` parses the TS interfaces and asserts that `/jobs`,
`/jobs/saved/all`, `/profile` and `/profile/preferences` return every declared field. It also checks that snake_case
writes still work. Verified 2026-09-24: passes on main; fails on the branch (`per_page`, `job_id`, `saved_at`,
`display_name`, ... missing).

## Postmortem (short)

- **Impact:** degraded UI for 3 days, and user preference data lost for users who saved their profile.
- **Why it shipped:** the review looked at the Python diff, not the serialized output; no cross-app test.
- **Lessons:** the JSON shape is a public API even when the only consumer is our own frontend. A read regression plus a
  form that re-submits what it read turns into a write regression.
