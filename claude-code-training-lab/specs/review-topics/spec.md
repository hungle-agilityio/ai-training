# Spec: review-topics

## Summary

Each review belongs to the topics whose keywords appear in its text. A new page `/topics/` ("Topics" in the sidebar) lists the seven topics with their counts, share, bad reviews and average rating, filtered by location and period. The Reviews page gets a "Topic" filter and shows topic labels on each review. The location page gets a "What customers talk about" panel and the Monthly report a "Topics" panel. No migration, no external service.

## Definitions

- **Topics and keywords** (in this order; this order is "the topic order"):

  | Slug | Label | Keywords |
  |---|---|---|
  | `wait` | Wait time | wait, queue, slow, delay, chờ, cho doi, đợi |
  | `staff` | Staff | staff, front desk, reception, nurse, nhân viên, lễ tân |
  | `care` | Doctor & treatment | doctor, care, treatment, bác sĩ, điều trị, đau |
  | `price` | Price & billing | price, expensive, bill, charge, cost, giá, đắt |
  | `booking` | Booking & phone | book, appointment, phone, call, đặt lịch, điện thoại, gọi |
  | `parking` | Parking | parking, car park, gửi xe, đỗ xe |
  | `cleanliness` | Cleanliness | clean, dirty, hygiene, smell, sạch, bẩn |

- **A review mentions a topic** when one of the topic's keywords, normalised with `normalize_for_search`, is part of the review's stored `search_text` (letter case ignored, accents count, anywhere in the text, as the review search does). A review can mention several topics, or none.
- **Bad review:** rating 1 or 2 (`RATING_RANGES["bad"]`).
- **Average rating:** `average_from_totals` in `reviews/services.py` (one decimal, half up; no reviews means no average, shown as "–").
- **Percent:** a whole number rounded half up (never `round()`), for example 4 of 14 is 29%.
- **Period:** "All time" (default), "Last 30 days" or "Last 90 days": reviews with `created_at` at or after now minus 30 (or 90) days.
- **Demo numbers** below are for `seed_demo_data` (14 reviews), all time, all locations.

## Acceptance criteria

Topic rules and totals (T1):

- **AC1.** `reviews/topics.py` holds the topics of the Definitions as a tuple `TOPICS` of frozen dataclasses `Topic(slug: str, label: str, keywords: tuple[str, ...])` in the topic order, `topic_by_slug(slug) -> Topic | None`, and `topics_of(text) -> tuple[Topic, ...]` (the topics a text mentions, in the topic order).
- **AC2.** On the 14 demo reviews `topics_of` gives: "Waited 50 minutes, nobody apologized." → Wait time; "Front desk understaffed, queue out the door." → Wait time, Staff; "Doctor was great but check-in was slow." → Wait time, Doctor & treatment; "Billing mistake and nobody called back." → Price & billing, Booking & phone; "Friendly staff, quick visit." → Staff; "Clean and efficient." → Cleanliness; "Parking is expensive." → Price & billing, Parking; "Đau chân đỡ hẳn, nhân viên thân thiện" → Staff, Doctor & treatment; "Dau dau khi cho doi" → Wait time; "Good care, parking is hard." → Doctor & treatment, Parking; "Best clinic experience I've had." → none; "Phone line always busy, could not book." → Booking & phone; "Bác sĩ tận tâm, ĐAU LƯNG đã đỡ nhiều" → Doctor & treatment; "Nhân viên lễ tân chưa nhiệt tình" → Staff.
- **AC3.** `reviews/topic_repository.py` is the only place that builds topic queries: `topic_condition(topic) -> Q` (a review mentions the topic, on `search_text`), and totals per topic (reviews, bad reviews, rating sum) plus the number of reviews and of reviews that mention no topic, for an optional location and an optional time range, in **one** query whatever the number of reviews or locations; and the totals of a month and of the month before, per topic, in one query.
- **AC4.** `reviews/topic_service.py` returns frozen dataclasses with plain values for the three uses below: the Topics page (AC6 to AC9), the location panel (AC17) and the report panel (AC19). Every count is an `int`, every average a `float` or `None`, every percent an `int`.
- **AC5.** Demo numbers, all time, all locations: 14 reviews, 1 mentions no topic. Doctor & treatment 4 reviews, 29%, 0 bad, 4.0; Staff 4, 29%, 2 bad (50%), 3.5; Wait time 4, 29%, 2 bad (50%), 2.5; Booking & phone 2, 14%, 2 bad (100%), 1.5; Parking 2, 14%, 0 bad, 3.5; Price & billing 2, 14%, 1 bad (50%), 2.0; Cleanliness 1, 7%, 0 bad, 4.0.

Topics page (T2):

- **AC6.** `/topics/` (URL name `topics`) has the title "Topics · ReviewRadar", heading "Topics", subtitle "What customers talk about, by topic.", no Export JSON button, and needs sign-in like every page. The sidebar shows a "Topics" item between "Reports" and "Reply drafts", marked current (`is-active`, `aria-current="page"`) on this page.
- **AC7.** A filter form (GET) with "Location" (`name="location"`, "All locations" then every location by name) and "Period" (`name="period"`: "All time" value empty, "Last 30 days" value `30`, "Last 90 days" value `90`) and an "Apply" button. A wrong or unknown value is ignored and the other one still applies (Django form in `reviews/topic_forms.py`).
- **AC8.** A line `id="topics-summary"`: "<n> reviews" ("1 review"), followed by " · <m> mention no topic" ("1 mentions no topic") when m > 0. Demo: "14 reviews · 1 mentions no topic". A table `id="topics-table"` inside `table-wrap` with the columns Topic, Reviews, Share, Bad, Average rating and a last column with a "See reviews" link. All seven topics are listed: most reviews first, then label A to Z. Share is the percent of the selected reviews. Bad shows "<n> (<p>%)" of that topic's reviews, or "0". A topic with no reviews shows 0, "0%", "0", "–" and no link.
- **AC9.** "See reviews" links to `/reviews/?topic=<slug>`, plus `&location=<id>` when a location is chosen (the period is not passed).
- **AC10.** No review in the database at all: an empty block "No reviews yet" with "Topics will appear here as soon as there are reviews." and no table. A selection with no reviews (a location without reviews, or a period without reviews): the summary "0 reviews" and the table with every topic at 0 and "–".
- **AC11.** The page makes at most 2 queries with 200 locations and 500 reviews. The view (`reviews/topic_views.py`) is thin: form, one service call, render. At 360 px the page does not scroll sideways (the table scrolls inside `table-wrap`); only the classes of `app.css`, light and dark, no new CSS file.

Reviews page (T3, T4):

- **AC12.** The filter form of `/reviews/` gets a "Topic" select (`id="filter-topic"`, `name="topic"`) after "Rating": "All topics" (value empty), then the seven labels in the topic order with their slugs as values. The chosen one is `selected`.
- **AC13.** `?topic=<slug>` keeps only the reviews that mention that topic and combines with search, location, rating, reply and week. An unknown slug is ignored. The topic is kept in the page links and in the Export CSV link (added after the other filters, so existing links do not change) and counts as a filter for "Clear" and "No reviews found". Demo: `?topic=wait` shows 4 reviews; `?topic=wait&rating=bad` shows 2.
- **AC14.** The Reviews page stays at most 3 queries with a topic filter (as `test_filtered_page_query_count`).
- **AC15.** In each review row, the Sentiment cell shows after the sentiment badge one label per topic the review mentions, in the topic order: `<span class="badge badge-neutral topic-label">Wait time</span>`. A review with no topic shows no label. The labels add no query and are outside the blurred `data-sensitive` text cell.

Location page (T5):

- **AC16.** `/locations/<id>/` gets a panel `id="location-topics"` with the heading "What customers talk about" and the line "Top topics of all reviews", after "Weekly trend" and before "Latest reviews".
- **AC17.** It lists the top 3 topics of that location with at least one review (most reviews first, then label A to Z): the label as a link to `/reviews/?location=<id>&topic=<slug>`, "<n> reviews" ("1 review"), and " · <b> bad" when b > 0. Demo: Airport: Wait time 3 reviews · 2 bad; Booking & phone 1 review · 1 bad; Doctor & treatment 1 review. Downtown: Staff 2 reviews; Cleanliness 1 review; Doctor & treatment 1 review. Riverside: Doctor & treatment 2 reviews; Booking & phone 1 review · 1 bad; Parking 1 review.
- **AC18.** When the location has no review that mentions a topic: "No topics yet" and no list, and no `badge-` class in the page content (existing test). The page needs at most 5 queries (one more than today).

Monthly report (T6):

- **AC19.** `/reports/` gets a panel `id="report-topics"` after the "Locations" panel, heading "Topics", line "Reviews per topic in <month label>". A table with the columns Topic, Reviews, Bad and "Change vs <previous month name>" lists the topics with at least one review in the chosen month or the month before, most reviews first, then label A to Z. Change is the difference in reviews: "▲ <n>" (`change-up`), "▼ <n>" (`change-down`) or "0" (`change-same`), with the aria-labels of the score change column ("Up <n> from <month>", "Down <n> from <month>", "Same as <month>").
- **AC20.** No topic in both months: "No topics this month." and no table. The months are the report's months (Vietnam time). The Monthly report CSV does not change. The page needs at most 2 queries (one more than today); the export at most 2.

## Edge cases

- Empty: no reviews (AC10), a location with no topic (AC18), a month with no topic (AC20).
- Large data: totals are one query each (AC3), never one per topic or per review; the Reviews page labels are computed from the row text already loaded.
- A keyword inside a longer word counts ("staff" in "understaffed", "book" in "booking"), as the search does; the list was checked on the demo texts (AC2).
- Permissions: every signed-in user, as on the other pages (there are no roles).
- Security: the `topic`, `location` and `period` values pass through Django forms; an unknown value is ignored. Review text is never put in a link or a log.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Feature | Review topics | In-app alerts; per-branch access | No migration or external service; every task can be built by the loop |
| Q2 Topic list | The seven topics and keywords of the Definitions | Owner edits keywords first | Checked on the demo texts (AC2) |
| Q3 Matching | Every topic whose keyword appears | Only the first topic | A review about waiting and staff counts for both |
| Q4 No topic | Counted in the Topics summary, no filter | Ignored | Shows how much the list misses |
| Q5 Topics page | `/topics/`, sidebar after Reports, Location and Period filters | No filters | Managers compare locations and recent weeks |
| Q6 Columns | Reviews, Share, Bad, Average rating, See reviews | Count only | Bad share and average show where it hurts |
| Q7 Reviews filter | Topic dropdown, kept in links and Export CSV | No filter | "See reviews" needs it |
| Q8 Labels | Topic labels on each review row | None | Reading the list shows the topics at a glance |
| Q9 Location page | Top 3 topics panel | None | The topics of one location where the manager looks |
| Q10 Monthly report | Topics panel with change vs previous month, page only | Also in CSV; none | Month-to-month view without changing the CSV contract |
| Q11 Empty states | "No reviews yet"; zero rows with "–" | Hide the table | The table shape stays the same |

## Design

`design/review-topics/README.md`

## Open questions
