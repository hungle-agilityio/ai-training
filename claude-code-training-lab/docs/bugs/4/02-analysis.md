# [FEAT] Filter reviews by good or bad: analysis and questions

- **ID:** 4
- **Reviewed on:** 2026-10-14
- **Status:** Waiting for reporter
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`, `dashboard`, `needs-info`
- **Where:** Not decided yet. Today the app has only one page, the Dashboard (`/dashboard/` on the dev environment), which shows one line per location with its number of reviews and average score. There is **no page that lists individual reviews**, so this is either a new "Reviews" page or filters added to the Dashboard.

## Analysis (3 sentences)

1. **What it asks:** Managers want to see only good or only bad reviews, and only the reviews of a chosen week, to prepare the weekly meeting. Because no screen shows individual reviews today, this means creating a new review list or adding filters to the Dashboard.
2. **What is ambiguous:** We don't know what counts as "good" or "bad" (a star rating range, or the sentiment the app detects automatically?), what "week" means (Monday to Sunday, or the last 7 days, and in which time zone), which screen should get the filters, and whether the filters can be combined or limited to one location. The app already stores a rating and a date for every review, so both filters are possible once these points are decided.
3. **First step:** Send the questions below to Marcus and write his answers into this ticket as acceptance criteria (a list of "when X, the screen must show Y"). Implementation starts only after Marcus confirms them.

## What we found so far

Today the app has no page that lists individual reviews. The Dashboard only shows, for each location, its number of reviews and average score.

## Questions for the reporter

1. What is a good review and what is a bad one? Our proposal: 4-5 stars good, 1-2 stars bad, 3 stars neutral (visible only when no filter is chosen). Or should it use the automatic sentiment instead?
2. What is a week: Monday to Sunday of a week the manager picks, or the last 7 days? In which time zone?
3. Where should it be: a new "Reviews" page, or filters on the existing Dashboard? For one location, all locations, or both?
4. Can the filters be combined (for example bad reviews of last week)? Should the filter also change the scores on the Dashboard, or only the list?
5. What should each review line show (location, stars, text, date)? Do you have a sketch?
