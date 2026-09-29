# M4: A keyboard user can't open a job or save it

**Context**
- `frontend/src/components/JobCard.tsx`: the whole card is a `<div onClick>`. The save/HN buttons have `opacity-0
  group-hover:opacity-100` and `title` but no accessible name.
- `frontend/src/components/JobDrawer.tsx`:
  - The drawer is two `div`s with no dialog role.
  - The close button contains only an `<X>` icon.
  - Escape works, but focus never moves into the drawer and isn't returned afterwards.
  - The match breakdown shows pass/fail only by colour (green vs grey with the same icon).

**Ticket.**
> A user who navigates by keyboard and screen reader reports they cannot open job details or save a job on the
> dashboard. Fix the job card and drawer to WCAG 2.2 AA for these flows.

**Constraints.** Keep the visual design. No new UI library. Tailwind is available (`focus-visible:` utilities).

**Definition of done**
- Tab to a card → Enter opens the drawer → focus lands in the drawer → Tab stays inside → Escape closes → focus returns
  to the card that opened it.
- The save button is reachable and visible on focus, and announces "Save job"/"Saved" (`aria-pressed`).
- The breakdown conveys matched/unmatched as text, not colour alone.
- Tests: add React Testing Library + `@testing-library/user-event` (the repo has no frontend tests yet), plus a manual
  NVDA or VoiceOver pass written up in the PR.

**Explain before touching**
1. A card with a click handler that also contains buttons and links: why is making the whole card a `<button>` wrong,
   and what's the usual pattern?
2. What must a modal dialog do about focus when it opens and closes? What about the page behind it?
3. How does `opacity-0` differ from `display:none`/`visibility:hidden` for keyboard and screen-reader users here?

See `curriculum/11-accessibility-essentials.md`. Answer: `training/_answers/ladder/mid-04.md`
