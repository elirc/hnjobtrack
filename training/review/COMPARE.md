# Compare your review with the model review

Fill this in **after** writing your own review and before re-reading the code.

| Model finding # | Did I find it? (yes / partly / no) | My severity vs model's | If missed: what would have led me to it? |
|---|---|---|---|
| R1 | | | |
| R2 | | | |
| … | | | |

**Findings I had that the model didn't** (and whether they hold up):

-

**The pattern behind my misses.** Pick the ones that apply and give one example each:
- [ ] I read handlers but not the *database's* guarantees (grants, RLS, enums, constraints)
- [ ] I trusted docstrings/README instead of checking the library's actual behaviour
- [ ] I didn't ask "what runs on the same event loop / process as this?"
- [ ] I didn't follow data across the API ↔ frontend boundary
- [ ] I treated model (LLM) output as trusted data
- [ ] I didn't think about background jobs failing silently
- [ ] I didn't run anything

**One habit I'll change in my next review:**
