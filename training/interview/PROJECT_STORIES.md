# STAR stories from HN Jobs (fill these in after doing the work)

Each story is a skeleton. Replace every `…` with what *you* did and measured. Never claim numbers you didn't produce.

## 1. Debugging: "the whole API stalled once a month" (INC-002)
- **S:** a FastAPI job board; the monthly LLM parse shared the event loop with HTTP traffic.
- **T:** find out why `/health` timed out while CPU was idle.
- **A:** … (heartbeat measurement, found `time.sleep` in async code, fix, ruff ASYNC rules)
- **R:** loop stall went from … s to < … s; the regression test is …

## 2. Trade-off: "who does the database think is asking?" (INC-004 / S1)
- **S:** a service-role backend; correct RLS policies that protected nothing on the API path.
- **T:** add database-enforced isolation without regressions.
- **A:** … (per-request client, kept explicit filters, concurrency test, lab probes)
- **R:** …; the trade-off you accepted: …

## 3. Incident: "a backend refactor deleted user data through the frontend" (INC-003)
- **S/T:** a camelCase serialization change; the UI re-submitted half-empty forms.
- **A:** … (rollback decision, data repair plan, consumer-driven contract test)
- **R:** …

## 4. Security finding: "the public key could edit listings" (review R1, ladder M3)
- **A:** … (built the RLS lab, ran probes, migration, verified before/after)
- **R:** P7/P8 went from allowed to 42501; reads unchanged.

## 5. Agent-caught / agent-introduced bug (agentic exercise)
- **A:** … (what the implementer agent produced, what the reviewer caught, what *you* caught that both missed)
- **R:** …; your rule for AI diffs now is …
