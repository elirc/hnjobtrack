# Practice

Every exercise runs against the code as it is, with the standard library only. Run all checks from `backend`:

```bash
python -X utf8 -m unittest discover -s tests -p "test_scraper*.py" -v
```

Before each exercise, write your prediction down, then make the test prove or disprove it. The 501-comment batching test and the "raise on the second batch" fake already exist in `test_scraper_recovery.py`; read them first instead of rewriting them.

## Exercise 1: scope is an exact integer match

**Goal:** In `ResumeImportTests` (`test_scraper_resume.py`), add a test that calls `_import_comments(FakeDB(None), "t", "42", rows)` with two comments: one with no `parent_id` key, and one whose `parent_id` is the string `"42"`. Predict the return value and the number of recorded calls before running it.

**Check:** The test asserts the return value is `0` and `db.calls == []`, and the suite stays green. Then explain from `scraper.py:90` why the string `"42"` is rejected (`c.get("parent_id") == int(hn_post_id)` compares against an int) and what would happen to every listing if Algolia ever returned `parent_id` as a string.

## Exercise 2: a duplicate inside one batch

**Goal:** In `RecoveryTests`, run `self.run_scrape(Database("pending"), HTTP(rows))` where `rows` holds comment `"7"` twice (both `parent_id: 42`), first with text `"first"` then `"second"`.

**Check:** Assert `len(db.rows) == 1` and `db.rows[("thread-1", "7")]["raw_text"] == "first"`. Then explain why the filter at `scraper.py:83-91` does not deduplicate, and why `ignore_duplicates=True` (PostgreSQL `ON CONFLICT DO NOTHING`) keeps the first row of the statement instead of raising the "cannot affect row a second time" error that a merge-style upsert would.

## Exercise 3: graduation fixture

**Goal:** In `RecoveryTests`, build a fixture of `comments(1001)` plus two duplicate copies of existing ids, one nested reply (`parent_id: 9`), and one empty body with `parent_id: 42`. Predict the batch sizes and the final row count before running a fresh `Database()` scrape.

**Check:** Assert `[len(v) for t, _, v, _ in db.calls if t == "job_listings"] == [500, 500, 3]` and `len(db.rows) == 1001`. Explain why there are 1,003 attempted rows but only 1,001 stored, and why the database constraint, not a preflight read, is the final authority when two workers interleave.

## Exercise 4: month extraction

**Goal:** Add a test for the pure helper `_extract_month` (`scraper.py:129-140`).

**Check:** `"Ask HN: Who is hiring? (January 2025)"` returns `"2025-01-01"`, and a title with no `(Month YYYY)` returns `datetime.now().strftime("%Y-%m-01")`. Then name the production risk of that silent fallback (a mis-titled thread gets the current month, not an error).

## Exercise 5: written design (no code)

**Goal:** Propose a reparse policy. `parse_thread_jobs` (`backend/app/services/parser.py:35-90`) marks the thread `done` even when some rows failed and were only flagged (`is_flagged: True`, `parsed_at` still null), and the scraper returns early for `done` threads (`scraper.py:43-44`).

**Check:** Your answer states (a) which rows a later `parse_thread_jobs(thread_id)` call would retry (its query is `.is_("parsed_at", "null")`, line 43), (b) whether comments posted after the thread became `done` are ever imported, and (c) one line of code or schema you would change, citing the file and line.
