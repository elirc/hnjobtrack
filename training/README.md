# HN Jobs apprenticeship pack (B06, LAB tier)

This is training material built on this repo: a FastAPI + Supabase (Postgres/RLS) + Next.js job board with an LLM
parsing pipeline. The skills it targets are the ones thin in the competency graph:
- **database-enforced isolation** (Postgres RLS as defense in depth, tenant-aware background jobs, noisy neighbours);
- **Python/FastAPI async correctness**;
- **LLM output boundaries**;
- **API contracts with a React frontend**;
- **accessibility**.

Answers are sealed in `_answers/`: don't open them until you've written your own.

## Suggested order (about 34 hours total)

| # | What | Where | Time |
|---|---|---|---|
| 0 | Set up the lab and run the RLS probes once | `lab/README.md` | 1 h |
| 1 | Blind review (60 min), then compare | `review/EXERCISE.md`, `review/COMPARE.md` | 2 h |
| 2 | Read the architecture, then the first-change page | `navigation/ARCHITECTURE.md`, `navigation/FIRST_CHANGE.md` | 1 h |
| 3 | Junior rung | `ladder/junior-01..03` | 5 h |
| 4 | Incidents 002 → 005 → 003 → 004 → 001 (easiest mechanism first) | `incidents/` + branches `training/incidents/*` | 5 h |
| 5 | Mid rung | `ladder/mid-01..04` | 9 h |
| 6 | "Why?" drills + change request | `navigation/TRADEOFFS.md`, `navigation/CHANGE_REQUEST.md` | 2 h |
| 7 | Agentic workflow | `agentic/WORKFLOW.md` | 3 h |
| 8 | Senior rung (design docs) | `ladder/senior-01`, `senior-02` | 4 h |
| 9 | Interview kit: questions, system design, mock defense, flashcards, stories | `interview/` | 2 h + ongoing |

## Index

- `lab/`: `fake_supabase.py`, `rls/rls_lab.py` (probe table of what each Postgres role can do), `fixtures/` (recorded model output).
- `ladder/`:
  - J1 first-time-user 500s · J2 404 vs 500 · J3 reset preferences + delete policy
  - M1 For You at scale · M2 search injection + FTS · M3 lock down public tables · M4 keyboard/screen reader
  - S1 Teams tenancy with RLS · S2 pipeline out of the API
- `review/`: a 60-minute blind review plus the compare template.
- `incidents/`: 5 briefs; the code is on branches `training/incidents/001..005-*` (see each brief).
- `navigation/`: architecture with evidence, first-change guide, 5 "Why?" drills, a change request.
- `agentic/`: the spec → agent → adversarial reviewer → verify → explain workflow, with a checklist.
- `interview/`: stories, 20 technical questions, system design, mock-defense script, 25 flashcards.
- `_answers/`: sealed answers, fix patches, the reference migration, and runnable regression tests
  (`_answers/regression-tests/`).

## Concept pages (central curriculum; linked, not repeated here)

In `C:\Users\Owner\Desktop\opusorganize\apprenticeship\curriculum\`:
- 02 idempotency
- 07 zero-downtime migrations
- 10 query plans
- 11 accessibility
- 14 load/back-pressure/retries
- 15 LLM features in production

## Existing learning docs in this repo

`astraupskill/` (an older codebase map, concepts, worked change, trace lab) was left untouched. It covers the scraper's
resumable import. This pack doesn't repeat it.
