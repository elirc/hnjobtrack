# INC-005 answer: a prompt change exposed a missing validation boundary

## Symptom

The December thread got stuck at `status: parsing`, with 214 of 1,012 listings parsed. Re-runs added almost nothing.
The only error was a single APScheduler traceback showing Postgres `22P02 invalid input value for enum role_type_enum`.
No alert fired, and instant digests weren't sent.

## Diagnostic path

1. Read the traceback bottom-up. The failure is a **DB write** (`parser.py:89`), not the model call. The value
   `"full-time, contract"` is exactly what the new prompt asks the model for.
2. Why 214: `parse_thread_jobs` gathers a batch of 20, then writes results one by one. The first out-of-enum answer
   raises out of the loop, which ends the whole function. Earlier batches and the rows before the bad one are saved;
   everything after it isn't, and the thread status never reaches `done`.
3. Why re-runs barely help: each run re-selects unparsed rows in the same order and hits a multi-type answer again early
   (roughly a third of posts are multi-role). A run moves forward only when the bad row lands late in a batch (+15 once),
   and then stops at the next one.
4. Is it the prompt or main? Run the fixture-based test on **main**: it fails the same way. The prompt only supplied the
   input; the fragile write path was already there.

## Root cause

- `backend/app/services/parser.py:72` (both main and branch): `role_type` (and every other field) goes from the model's
  JSON straight to the DB with no schema validation.
- `parser.py:60-89`: only model-call exceptions are caught per row. A **write** failure isn't isolated, so one bad row
  aborts the thread.
- `parser.py:12` (branch): the prompt invites values outside `role_type_enum` (`supabase/schema.sql:92`).
- The same unvalidated boundary feeds the UI and email: `apply_url` is rendered as a link (`JobDrawer.tsx`) and
  company/role go into email HTML (`notifications.py`) without checks.

## Fix

`training/_answers/incidents/005-fix.patch` (verified 2026-09-24: 2/2 tests pass):
- A `ParsedListing` pydantic model using the existing `RoleType`/`RemoteType` enums is the contract between model and DB.
  A validator keeps the first valid type from a comma-joined value.
- Each row is handled in its own try/except: any failure (model, validation or write) flags that row, logs it, and the loop
  continues. The thread always reaches `done`.
- The prompt goes back to "exactly one value". If multi-type posts matter to the product, model them explicitly (a
  `role_types role_type_enum[]` column via expand/contract), not by string-joining into an enum.

## Regression test

`training/_answers/regression-tests/test_inc005_llm_output_boundary.py` uses the recorded answers in
`training/lab/fixtures/parse_multirole.json` (hand-written; no API calls). It asserts that all valid rows are parsed, the
thread finishes, and bad rows are normalized or flagged. Fails on the branch **and on main**; passes with the fix.

## Postmortem (short)

- **Impact:** most of December's listings missing for 2+ days; instant digests not sent. No data corrupted.
- **Why it shipped:** "prompt-only change" was treated as low-risk; no eval runs prompt changes against a golden set
  checked by the output schema; background-job failures don't alert.
- **Action items:**
  - an eval gate for prompt PRs: a golden set of recorded HN posts, schema-validity rate, field accuracy
  - alert when a thread stays in `parsing` longer than N hours, or when the parsed share is below X%
  - alert on APScheduler job exceptions
  - validate every model output before it reaches the DB, the UI or an email

See `curriculum/15-llm-features-in-production.md`.
