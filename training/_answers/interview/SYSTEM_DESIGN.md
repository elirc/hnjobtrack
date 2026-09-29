# System design rubric (10 points)

| Area | Strong answer includes | pts |
|---|---|---|
| Ingestion | per-source workers plus a durable queue; per-source and per-model rate limits; a DLQ; resumable items (reuses the `unique(thread_id, hn_comment_id)` idea generalized to `(source, external_id)`) | 2 |
| Parse cost | a back-of-envelope estimate (e.g. 200k × ~1.5k tokens ≈ 300M tokens/month, priced with the current model rate and batch discount); `prompt_version` per row plus selective re-parse; heuristics before the LLM | 1 |
| Search | Postgres FTS until facets or relevance need more; the migration via CDC/outbox to a search index; Postgres stays the source of truth | 1 |
| For You | precomputed candidate sets refreshed on new listings or pref changes; per-request re-ranking of the top N; clear freshness SLA | 1 |
| Tenancy | row-level plus RLS as the default with a named escape hatch (dedicated database) for residency tenants; per-tenant fairness and budgets in jobs; policy performance (`(select auth.uid())`, indexed membership) | 2 |
| Multi-region | listings replicated read-only everywhere; user and tenant data pinned to a home region; auth per region or with a residency-aware IdP | 1 |
| Failure | idempotent digest sends (key + provider idempotency) so failover means resend-safe; what's lost vs duplicated, stated explicitly | 2 |

Red flags:
- "Just add Kubernetes" with no queue or state design.
- No cost estimate.
- Tenancy by app filters only.
- Ignoring that the LLM is an unreliable dependency.
