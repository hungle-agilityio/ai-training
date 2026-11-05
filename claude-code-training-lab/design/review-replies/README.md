# Design: review-replies

Design card: https://claude.ai/artifact/9b1MnxExraTu7EwmgMJgZr

Four boards, demo data from `seed_demo_data` after T6 (the 14 reviews 0, 20, 40, 60 and 80 days back; replies on the six 4 and 5 star reviews), seeded and opened on Thursday Nov 5, 2026 (Vietnam time):

1. **Reply drafts (normal):** `/replies/` with "Reply drafts" active in the sidebar (no "Soon"), "8 reviews need a reply", the 8 reviews in the order of AC10 (Riverside 2★ Aug 17, Airport 1★ Sep 6, Riverside 2★ Sep 26, Airport 2★ Oct 16, Airport 2★ today, then the 3★ reviews oldest first) and a "Reply" button on each row.
2. **Reply page:** `/reviews/<id>/reply/` for Airport 2★ "Waited 50 minutes, nobody apologized.": the review, the "Your reply" box with its hint, "Save reply", "Back to reply drafts", "Last saved … by demo", and the red line of AC19 (shown only after a wrong reply).
3. **Dashboard tile and review list:** the fifth KPI tile "Need a reply 8" with "Open reply drafts"; the Reviews page with the "Reply" filter and the "Reply" column ("Replied" / "Not replied" badge, "Edit reply" / "Reply" link).
4. **Saved, empty, narrow:** "Reply saved." and 7 left after answering the Airport review; "All caught up / Every review has a reply."; the tile at 0; the queue at 360px with the table scrolling inside its panel.

The build must use the texts on the card (they are also in `specs/review-replies/spec.md`) and the app's own colours from `app.css`, in light and dark. The demo reply text in board 2 is an example typed by staff; the seed uses the text of AC31. The dashed pink outline only marks what is new.
