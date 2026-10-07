# Verification

> Status note (2026-10-06): this is the original 2026-09-21 record. Re-running `python -X utf8 -m unittest discover -s tests -p "test_scraper*.py" -v` from `backend` with Python 3.13 still gives 9 tests, OK. The `cwd` in `evidence/results.json` is the original author's staging path, not a path in this repo.

The staged regression commands passed: the resume suite ran 3 tests and the recovery suite ran 6 tests, for 9 total. The tests use fake HTTP/database-adjacent objects and do not contact Algolia, Supabase, GPT, email, or notifications. They verify new-parent creation, pagination, failure after parent creation, partial-batch retry, parsed-field preservation, completed-thread early return, filtering/error handling, and no-story handling. The schema was reviewed to ensure the conflict target has a guarded migration.

This evidence does not establish that the installed Supabase client accepts every fake call shape, that the remote API’s pagination metadata is complete, or that an interrupted transaction leaves exactly the assumed parent row. Those limits should guide the next integration check. A reviewer can run the test without installing third-party dependencies because the test stubs `httpx` and the Supabase module before importing the service. The checks ran in an isolated copy; the report records delivery separately and preserves exact original source snapshots.

For a higher confidence release check, apply the schema in an isolated database, run the importer twice against a recorded fixture, and assert one row per `(thread_id, hn_comment_id)` while checking that parsed columns survive duplicate-ignore repair. That isolated check was not executed here; current evidence is limited to nine fake-boundary cases and static schema review.

The handoff records these limits alongside the command and result so a reviewer can distinguish executable evidence from a proposed next check. That distinction matters for CRUD changes: a fake proves the intended call contract, while a real database proves constraints, merge semantics, permissions, and transaction behavior. Both are useful, but they answer different questions and should not be reported as interchangeable.

The intended client options follow the [Supabase upsert reference](https://supabase.com/docs/reference/python/upsert) and the [PostgREST conflict-target reference](https://docs.postgrest.org/en/v14/references/api/tables_views.html); those contracts were not exercised against a live service.

Apply the separate [existing-database migration](../supabase/migrations/20260921_job_comment_unique.sql) before using the new conflict target on an existing installation. It deliberately fails if duplicate logical keys already exist: review those rows rather than deleting parsed records automatically. Fresh installs declare the same named constraint in schema.sql. No migration was applied to a live database during this task.

Accepted evidence: [nine-test output](evidence/astra-crud-b01-all-scraper.log), [exact command and limits](evidence/results.json).
