# Design: review-topics

Design card: https://claude.ai/artifact/XxMdyqVBUbnt8YdCBrFMQX

Six boards (demo data only, `seed_demo_data` seeded 2026-11-06):

1. **Topics page, all time:** sidebar item "Topics" between Reports and Reply drafts (current), Location and Period filters, the summary "14 reviews · 1 mentions no topic", `#topics-table` with the seven topics of AC5 and "See reviews" links (AC6 to AC9).
2. **Topics page, last 30 days and empty:** 6 reviews; topics with no reviews at the end with 0, "0%", "0", "–" and no link; the "No reviews yet" block when the database has no review (AC8, AC10).
3. **Reviews page:** the "Topic" select after "Rating" (`#filter-topic`), `?topic=wait` with 4 reviews, and the topic labels after the sentiment badge in each row (AC12 to AC15).
4. **Location page panel:** `#location-topics` "What customers talk about" for Airport (Wait time 3 reviews · 2 bad; Booking & phone 1 review · 1 bad; Doctor & treatment 1 review) and the "No topics yet" state (AC16 to AC18).
5. **Monthly report panel:** `#report-topics` for November 2026 with "Change vs October" (▲ 1, 0, ▼ 1) and "No topics this month." (AC19, AC20).
6. **Narrow, 360 px:** the filters stack, the table scrolls inside `table-wrap`, no sideways page scroll (AC11).

The build uses the texts of `specs/review-topics/spec.md` and the classes of `app.css` (`panel`, `panel-head`, `table`, `table-wrap`, `button`, `badge badge-neutral`, `change-up`, `change-down`, `change-same`), light and dark; no new CSS file. The dashed pink outline only marks what is new. Month numbers on board 5 depend on the day the demo data is seeded.
