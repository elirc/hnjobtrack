# M4 answer: keyboard and screen reader

1. **Card pattern.** Interactive elements can't be nested inside a `<button>` (invalid, and focus behaviour breaks).
   The usual pattern: make the **title** a real `<button>` (or a link to `/jobs/{id}`) that opens the drawer, and stretch
   its clickable area over the card with an `::after` pseudo-element. Keep the save button and the HN link as siblings
   with `relative z-10`. Screen readers then get one clear control per action.
2. **Dialog focus.** Give the drawer `role="dialog"`, `aria-modal="true"` and `aria-labelledby` pointing at the company
   heading.
   - On open: move focus to the dialog (the close button or the heading with `tabIndex=-1`).
   - While open: trap Tab inside and make the page behind inert (the `inert` attribute on the main content).
   - On close: return focus to the element that opened it (store `document.activeElement` on open).
   - The icon-only close button gets `aria-label="Close job details"`.
3. **opacity-0.** An opacity-0 button is still in the tab order and still announced, but invisible when focused: a
   sighted keyboard user lands on nothing. Add `focus-visible:opacity-100 group-focus-within:opacity-100`, or just show it.
   Touch devices have no hover at all.

Also:
- The save button: `aria-label` plus `aria-pressed={isSaved}`.
- The breakdown: add visually hidden text ("Skills: matched" / "not matched") or different icons, not colour alone (WCAG 1.4.1).
- The `apply_url` link comes from model output: allow only `http(s)` schemes before rendering (see INC-005 and the review).

Tests with RTL + user-event: `await user.tab()` reaches the card, `{Enter}` opens the dialog,
`expect(dialog).toHaveFocus` / contains focus, `{Escape}` closes it, and focus is back on the card.
