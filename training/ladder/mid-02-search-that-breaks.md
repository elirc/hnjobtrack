# M2: Search breaks on "C++, Go" and ignores the full-text index

**Context.** `GET /jobs?search=...` (`backend/app/api/jobs.py:33-36`) builds a PostgREST `or=(...)` filter by putting the
raw search string into a filter expression (`ilike` on company/role/description plus `skills.cs.{...}`).
Meanwhile `supabase/schema.sql:127-137` defines a generated `fts tsvector` column with a GIN index that no query uses.
`README.md` says search uses "PostgreSQL tsvector indexing".

**Ticket.**
> Searches with commas, parentheses or quotes ("C++, Go", "Acme (YC W24)") return 500 or strange results. Also make
> search fast and ranked. The README promises full-text search, so make that true.

**Constraints.**
- User input must never become part of a filter *expression*. Treat it strictly as a value.
- Keep the existing filters (`remote`, `skills`, ...) combinable with search.

**Definition of done**
- Tests for the tricky inputs above plus an empty string and a very long string (200+ chars).
- Search uses the `fts` column (e.g. `text_search("fts", q, options={"type": "websearch", "config": "english"})`),
  plus a separate, explicit skills match.
- `EXPLAIN` from the RLS lab database shows the GIN index being used (the lab seed is tiny, so `set enable_seqscan = off`
  to demonstrate).

**Explain before touching**
1. Why is building a filter string from user input the same *class* of bug as SQL injection, even though PostgREST
   parameterizes its SQL? What can a user change today besides breaking the query?
2. `fts` covers company, role and description, but not `skills`. How should "python" match a job whose skills array has
   `Python` (capitalized)?
3. What's the trade-off between `ilike '%x%'` (substring, no index) and `websearch_to_tsquery` (stemmed, indexed)?
   Which user-visible behaviour changes?

See `curriculum/10-query-plans-and-indexes.md`. Answer: `training/_answers/ladder/mid-02.md`
