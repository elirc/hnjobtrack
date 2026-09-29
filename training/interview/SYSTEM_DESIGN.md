# System design: take HN Jobs to 50× and to enterprise tenants

**Prompt to answer (45 min, whiteboard):** HN Jobs becomes a general job-discovery product:
- 50 sources instead of one monthly HN thread, about 200k listings per month;
- 2M users, 500 enterprise tenants (bootcamps and agencies) with shared pipelines and SSO;
- EU and US users, with the EU's data kept in the EU.

Start from the current architecture (`training/navigation/ARCHITECTURE.md`), not from scratch.

## Pressure points (the interviewer pushes on these; have an answer for each)

1. **Ingestion.** One scheduler inside the API won't do. Where do the scrapers and the parse queue run, and how do you rate-limit
   per source and per LLM quota? What happens when the LLM provider is down for 6 hours?
2. **Parsing cost.** 200k posts/month × tokens × price: estimate it. When do you switch to batch APIs, a cheaper model, or
   heuristics first? How do you re-parse after a prompt change without re-paying for everything?
3. **Search.** Postgres FTS vs a search engine at 200k/month plus facets. What's the migration path from `fts`, and what stays in Postgres?
4. **For You at 2M users.** Per-request scoring vs precomputed candidates vs embeddings. What's the freshness requirement?
5. **Tenancy.** Row-level (org_id + RLS) vs schema-per-tenant vs database-per-tenant for 500 tenants, some wanting
   dedicated data residency. How does the digest pipeline stay fair when one tenant has 50k members?
6. **Multi-region.** Where do auth, listings (global, read-mostly) and user data (regional) live? What crosses regions?
7. **Failure.** Postgres primary failover during the digest run: what's sent twice, and what isn't sent at all?

## Follow-ups the interviewer uses
- "Your RLS policy does a membership lookup per row. The tenant with 50k saved jobs complains about latency. Now what?"
- "A prompt change corrupted 3 days of listings in one region. Walk me through detection, blast radius and repair."
- "Why not just give each tenant a Supabase project?"

Rubric: `training/_answers/interview/SYSTEM_DESIGN.md`
