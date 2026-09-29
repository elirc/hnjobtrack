# M2 answer: search as a value, not as syntax

1. **Why this is injection.** `jobs.py:34-36` interpolates user text into PostgREST's *filter language*. PostgREST
   escapes SQL correctly, but the `or=(...)` grammar treats commas, dots and parentheses as structure. User text can
   therefore change the *shape* of the filter (add or alter conditions, or make it unparseable, hence the 500s), which
   is the same class as SQL injection: data interpreted as code. The data exposed is public listings, so the risk is
   mostly integrity and availability, but the pattern must not spread to user-owned tables. The fix is structural:
   never format user input into a filter expression; pass it as a value to an API that quotes it (`text_search`,
   `ilike(col, pattern)` on a single column), or to an RPC with typed parameters.
2. **Skills matching.** The skills array is case-sensitive (`Python` vs `python`) and isn't in `fts`. Options: normalize
   skills to lower case at write time (the parser boundary from INC-005 is the right place) plus a lower-cased query;
   or add `array_to_string(skills,' ')` to the generated `fts` expression (a column rebuild, which is a migration).
3. **Trade-off.** `ilike '%x%'` gives substring matches ("Go" matches "Google") with no index, so it's a full scan.
   `websearch_to_tsquery('english', q)` is stemmed and uses the GIN index, and supports quotes and `-exclude`, but won't
   do partial words ("Postg" won't match). Behaviour changes, so tell product. Rank with `ts_rank` if sorting by relevance.

Reference: `query.text_search("fts", search, options={"type": "websearch", "config": "english"})`, plus
`.overlaps("skills", [normalized terms])` if you want skills included. Tests: the inputs from the ticket must return 200.
`EXPLAIN` in the lab should show a `Bitmap Index Scan on idx_job_listings_fts`.
