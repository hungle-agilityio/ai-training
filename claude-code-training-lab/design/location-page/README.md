# Design: location-page

Design card: https://claude.ai/artifact/XQ6E4muXrKbUq53iwWBKGH

Six boards, demo data from `seed_demo_data --with-new-branch`, seeded and opened on Monday Nov 2, 2026 (Vietnam time):

1. **Normal:** `/locations/<Riverside id>/`: Score 3.4, Watch, 5 reviews; rating breakdown 1/2/0/2/0; weekly trend with bars only for the weeks of Oct 26 (3.3, 4 reviews) and Nov 2 (4.0, 1 review) and "–" for the six weeks before; the trend table; the 5 newest reviews and "See all reviews".
2. **Empty:** `/locations/<Newtown id>/`: "No reviews yet", 0 counts, empty weeks, no "See all reviews" link.
3. **Error:** an unknown id shows the existing 404 page, unchanged.
4. **Links:** the dashboard's new "Details" column and the review list's location name link (the dashed pink outline marks what is new).
5. **Narrow screen:** 360px, panels stacked, all 8 trend columns visible.
6. **Rules:** score, status, week, bar height and `data-sensitive`.

The build must use the texts on the card (they are also in `specs/location-page/spec.md`) and the app's own colours from `app.css`, in light and dark. The dashed pink outline only marks what is new.
