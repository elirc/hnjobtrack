# Change request: "Hide jobs I've dismissed"

> **From the PM:** On For You and the dashboard, users want a "Not interested" button on a job. Dismissed jobs never
> show again in lists, For You, or the digest emails. There's an "Undo" toast for 5 seconds, and a "Dismissed" tab on
> the Saved page where they can restore them. Dismissals are private to the user.

Before any agent writes code, write down (1 page max):

1. **Data:** a new table or a new `saved_jobs.status` value? Constraints, indexes, RLS policies (all four commands?),
   and the migration file name.
2. **API:** endpoints (method, path, status codes), idempotency of dismiss/undo, and which existing endpoints change
   (`list_jobs`, `for_you_jobs`, `send_digest_notifications`), with the exact files.
3. **Query strategy:** how `/jobs` excludes dismissed jobs without breaking `count="exact"` pagination, for anonymous
   vs. signed-in users (`get_optional_user` exists but is unused).
4. **Frontend:** components touched, optimistic update plus rollback, and the toast's accessibility (live region,
   focus, 5-second timing vs WCAG 2.2.1).
5. **Tests:** what proves "never shows again" across all three surfaces, and what proves privacy.
6. **Risks:** which incident in `training/incidents/` is most likely to repeat here, and how your plan prevents it.

Reference placement: `training/_answers/navigation/CHANGE_REQUEST.md`
