# Design: reply-suggest

Design card: https://claude.ai/artifact/VrphuvyAFdoHNmPJyXfkER

Four boards on the reply page `/reviews/1/reply/` (demo data from `seed_demo_data`: Airport, 2 stars, "Waited 50 minutes, nobody apologized."):

1. **Normal:** the "Suggest a reply" button after "Save reply", outlined (secondary), and the hint "Claude writes a draft in the box. Nothing is saved until you press Save reply." (AC11).
2. **After a suggestion:** the line "Suggested by Claude. Read and edit it before you save." above the box, and the demo draft in the box, ending with a blank line and "— Airport team" (AC6, AC7, AC12).
3. **Error:** the red line "Could not get a suggestion right now. Try again or write your own." and the typed text kept (AC13).
4. **Narrow and off:** at 360px the buttons wrap with no sideways scroll (AC16); with no key on the live site the page is exactly as today (AC11).

The build must use the texts on the card (they are also in `specs/reply-suggest/spec.md`) and the app's own colours from `app.css`, in light and dark. The draft on the card is the fixed demo draft (`FAKE_REPLY_TEXT`); with a real key Claude writes it. The dashed pink outline only marks what is new.
