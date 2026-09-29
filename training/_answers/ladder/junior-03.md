# J3 answer

1. **Is the policy needed today?** With the service-role client the delete works without a policy (the service role
   bypasses RLS). The policy is still needed because (a) the frontend could call Supabase directly with the user's JWT,
   and (b) the planned move to user-scoped clients (S1, the INC-004 fix) would silently turn the endpoint into a no-op:
   `DELETE 0`, 204, nothing deleted. That is the worst kind of bug. The lab's probe P5 shows it.
   Reference migration: `create policy "Users can delete own preferences" on user_preferences for delete using (auth.uid() = user_id);`
   (it's included in `_answers/ladder/mid-03-lock-down-public-tables.sql`, verified: P5 goes from `DELETE 0` to `DELETE 1`).
2. **404 or 204?** 204 both times. DELETE is idempotent, and the client's goal ("no preferences") is met either way.
   A 404 would make retries look like failures.
3. **Frontend.** Reset every preference field's state to empty, and invalidate any cached For You data.
   - Confirm with a native `<dialog>` or `confirm()` for a first version.
   - After success, announce "Preferences reset" in a `role="status"` live region (the page already has a `message`
     state, so render it in one).
   - Move focus to the first form field or keep it on the button. Never let focus drop to `<body>`.

Grading: the strongest answers spot the "silent no-op after migrating to RLS" trap in question 1.
