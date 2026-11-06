# Spec: reply-speed

## Summary

The dashboard `/dashboard/` gets a sixth KPI card, "Replied in 24h", and the Location scores table gets a "Replied in 24h" column. They show the share of bad reviews (rating 1 to 2) that got a reply within 24 hours, and the card also shows the average time to reply. The demo data (`seed_demo_data`) gets replies to some bad reviews with fixed delays, so the live site shows real numbers. No migration; the dashboard API and the other pages do not change.

## Definitions

- **Bad review:** rating 1 or 2 (`rules/domain.md`).
- **Reply time:** `reply.created_at - review.created_at`. Editing a reply keeps `created_at`, so the first reply counts.
- **Counted bad review:** a bad review that has a reply, or that has no reply and was created more than 24 hours before now. A bad review with no reply that is 24 hours old or younger is still open and is not counted.
- **Replied in 24h:** a counted bad review whose reply time is 24 hours or less (exactly 24:00:00 counts). A counted bad review with no reply is a miss.
- Hours are clock hours. Time zones do not matter, because only the difference of two times is used.

## Acceptance criteria

Demo data (T1):

- **AC1.** `seed_demo_data` still replies to every review rated 4 or 5, with the same text, no author and the seed time, as today.
- **AC2.** It also replies to three bad reviews, with the text "We are sorry about your visit. Our manager will call you to make it right.", no author, and `created_at` = `updated_at` = the review's `created_at` plus a fixed delay: Airport "Front desk understaffed, queue out the door." + 30 hours; Riverside "Phone line always busy, could not book." + 3 hours; Riverside "Nhân viên lễ tân chưa nhiệt tình" + 20 hours.
- **AC3.** No other review gets a reply: Airport "Waited 50 minutes, nobody apologized." and "Billing mistake and nobody called back." and every 3-star review stay without one. The default seed makes 9 replies; each extra branch from `--branches` still gets 2; seeding twice still gives 9.

Dashboard (T2):

- **AC4.** A new KPI card `id="kpi-reply-speed"` with the label "Replied in 24h" is the sixth card, after "Need a reply". Its value is the replied-in-24h count divided by the counted count, as a whole percent rounded half up (2 of 3 shows "67%", 1 of 8 shows "13%"). Under it: "<replied> of <counted> bad reviews", then "Average reply time <time>".
- **AC5.** The average is the mean reply time of the counted bad reviews that have a reply, in hours, rounded half up to one decimal. Under 48 hours it shows as hours ("17.7 h"); from 48 hours it shows as days, the hours divided by 24 and rounded half up to one decimal ("2.0 days" for exactly 48 hours, "3.1 days" for 74.5 hours). The hours-or-days choice uses the value before rounding, so 47.96 hours shows "48.0 h". Never `round()` or `//` (`knowledge/KNOWN_PITFALLS.md`).
- **AC6.** With no counted bad review the value is "–" and the only hint is "No bad reviews yet". With counted bad reviews but none replied, the value is "0%", the first hint shows as in AC4 and the second hint is "No replies yet".
- **AC7.** The Location scores table (its panel gets `id="location-scores"`) has a new column "Replied in 24h" between "Status" and "Details". Each row shows that location's whole percent as in AC4, or a muted "–" when the location has no counted bad review (also for a location with no reviews).
- **AC8.** On a fresh `seed_demo_data` the card shows "50%", "2 of 4 bad reviews" and "Average reply time 17.7 h"; the column shows Airport "0%", Downtown "–", Riverside "100%".
- **AC9.** `/dashboard/` still makes exactly 3 database queries for any number of locations, and the existing `tests/integration/test_dashboard.py` passes unchanged. `/api/dashboard/` returns the same JSON as today. `reviews/views.py` does not change: `services.dashboard_overview` takes an optional `now` that defaults to the current time.
- **AC10.** The six cards show 3 per row above 1000 px and 2 per row below, as today. At 360 px the page does not scroll sideways; the table scrolls inside its own box as today. Colours come from the tokens in `app.css`, in light and dark.
- **AC11.** The percent is an `int` and the average hours a `float` (or `None`); tests assert the types.

## Edge cases

- Empty: no locations shows the existing "No locations yet" panel. Locations but no counted bad review: AC6.
- A bad review created less than 24 hours ago with no reply is not counted yet (it may still get its reply in time). The same review with a reply is counted at once.
- Large data: 200 locations still take 3 queries (AC9); the numbers come from aggregates, never from loading every review.
- Permissions: same as the dashboard today, every signed-in user; visitors who are not signed in are sent to sign-in.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Which reviews | Both the percent and the average on bad reviews (1 to 2) | Average on every replied review; all reviews | Bad reviews are the ones where speed loses customers; one base keeps the two numbers consistent |
| Q2 Bad review without a reply, older than 24 h | Counted as a miss | Left out | Leaving them out would make a location that never replies look perfect |
| Q3 Period | All time, like the other KPIs | Last 30 days | Same base as the other dashboard numbers; a filter can come later |
| Q4 Where | KPI card plus a column per location | KPI card only | The tool is about comparing locations |
| Q5 Average format | Mean, one decimal half up, hours under 48 h, days from 48 h | Always hours | "75.0 h" is harder to read than "3.1 days" |
| Q6 No bad reviews | "–" and "No bad reviews yet" | 100% | 100% would claim a result that was never measured |
| Q7 Demo data | Seed replies with fixed delays, some bad reviews in 24 h and some late; the existing test `test_seed_demo_replies.py` may be updated | Keep the seed, live site shows the empty state | Otherwise the live site cannot show the feature |
| Q8 What 24 h means | Clock hours | Business hours | No opening hours are stored |

## Design

`design/reply-speed/README.md`

## Open questions
