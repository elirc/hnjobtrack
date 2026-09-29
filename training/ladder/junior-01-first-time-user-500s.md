# J1: New users get "API error" on their first save

**Context.** HN Jobs uses supabase-py 2.11 / postgrest-py 0.19.3 (`backend/requirements.txt`). Several endpoints look up
an optional row with `.maybe_single().execute()` and then read `.data`:
`backend/app/api/saved.py:26`, `saved.py:60`, `api/profile.py:21,72,103`, `api/jobs.py:85,142`, `services/notifications.py:73`, `services/scraper.py:35`.

**Ticket.**
> Support: "I signed up, clicked the bookmark on my first job, and got a red 'API error'. Same when I first saved my
> preferences." Please fix it so a brand-new user's first save, first preferences save and For You page work.

**Constraints.** Don't change the DB schema. Keep the endpoint contracts (status codes, response shapes).

**Definition of done**
- `training/_answers/regression-tests/test_junior01_first_time_user.py` passes on your branch. It uses the real client
  library with a simulated PostgREST, so run it from `backend/` as described in `training/lab/README.md`.
- Every `maybe_single()` call site listed above is handled the same way, not just the three the test covers.
- A unit test in `backend/tests/` for your chosen helper, if you add one.

**Explain before touching** (write your answers down first)
1. What exactly does `.maybe_single().execute()` return when no row matches, in *this* library version? How will you prove
   it rather than trust the docs or an AI answer?
2. Why do `backend/tests/test_scraper_*.py` pass even though they cover a `maybe_single()` call site?
3. Which of the listed call sites run in background jobs rather than requests, and what does a crash there look like to a user?
4. Which option do you prefer, and why: a helper (`maybe_one(query) -> dict | None`), `.limit(1)` plus a list, or upgrading the library?

<details><summary>Hints</summary>

- The first 20 lines of `training/lab/README.md` show a two-line experiment that answers question 1.
- Check which month's scrape is the *first* one to reach `scraper.py:35` with no existing row.
</details>

Answer: `training/_answers/ladder/junior-01.md`
