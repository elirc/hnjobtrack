# J3: "Reset my preferences" button

**Context.** Preferences live in `user_preferences` (`supabase/schema.sql:51-72`). It has RLS policies for select,
insert and update, **but not delete**. The API has `GET/PUT /profile/preferences` (`backend/app/api/profile.py:65-131`).
The UI is `frontend/src/app/profile/page.tsx`.

**Ticket.**
> Users want a "Reset preferences" button that forgets their skills/roles/locations so For You falls back to "latest
> jobs". Add `DELETE /profile/preferences` and the button.

**Constraints**
- The endpoint must work the same whether the backend uses the service-role client (today) or a user-scoped client
  (ladder `senior-01`).
- The button needs a confirmation, and focus must go somewhere sensible afterwards. See `curriculum/11-accessibility-essentials.md`.

**Definition of done**
- The endpoint returns 204. It is idempotent (a second call also returns 204).
- There's a migration adding the missing delete policy, verified with the RLS lab: probe P5 goes from `DELETE 0` to
  `DELETE 1` (`training/lab/rls/rls_lab.py run <your.sql>`).
- The For You page after a reset shows the fallback list (`jobs.py:88-97`).
- API test (fake DB) plus the lab output pasted in the PR.

**Explain before touching**
1. With today's service-role client, would the endpoint work without the new policy? Then why add the policy at all?
2. Should DELETE of a non-existent row return 404 or 204? Defend it.
3. Which frontend state must reset, and what does a screen-reader user hear after pressing the button?

Answer: `training/_answers/ladder/junior-03.md`
