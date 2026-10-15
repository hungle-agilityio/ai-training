# [FEAT] Filter reviews by good or bad

- **Reporter:** Marcus, product owner
- **Reported on:** 2026-10-13
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`, `needs-info`

## Summary

Managers need to filter the list on the existing **Reviews** page (`/reviews/`) by location, by good or bad, and by week, to prepare the weekly meeting. The page already lists every review, newest first, 20 per page; this ticket adds the filters on top of it. The Dashboard does not change.

## Acceptance criteria

Items marked (proposal) are not yet confirmed by the reporter.
- When a manager opens the Reviews page without choosing anything, it lists the reviews of all locations, newest first, as it does today.
- When a manager chooses a location in the location dropdown, only that location's reviews are shown. The dropdown starts on "All locations". (proposal for the start value)
- When a manager chooses "good", only reviews rated 4 or 5 stars are shown.
- When a manager chooses "bad", only reviews rated 1 or 2 stars are shown.
- When no good or bad choice is made ("All ratings"), reviews of every rating are shown, including 3 stars. Reviews rated 3 stars are never shown when "good" or "bad" is chosen.
- When a manager chooses a week, only reviews written from Monday to Sunday of that week (Vietnam time, UTC+7) are shown. A review written on Sunday at 23:59 belongs to that week, and one written on the following Monday at 00:00 does not.
- The manager chooses a week by picking any day; the page then shows the Monday-to-Sunday week that contains that day, and tells which week is shown, for example "Oct 12 - Oct 18, 2026". (proposal)
- When a manager combines a location, a good or bad choice and a week, only reviews matching all of them are shown.
- When filters are chosen, the line under the table, for example "Showing 1-12 of 12 reviews", counts only the reviews that match.
- When the manager goes to another page of the results, the chosen filters stay. When the manager changes a filter, the list starts again from the first page. (proposal)
- The filters change only the list. The scores on the Dashboard do not change.
- When filters are chosen and no review matches, the page shows "No reviews found" instead of an empty table. When there are no reviews at all, it keeps showing "No reviews yet". (proposal)
- When the address contains a filter that does not exist (for example a week or a location that is not in the system), the page ignores that filter and shows the list as if it had not been chosen. (proposal)
- A location that has no reviews yet (for example Newtown) is in the dropdown, and choosing it shows "No reviews found". (proposal)
- The Sentiment column (Positive, Neutral, Negative) stays as it is today.

## What exists today

1. Open the Reviews page (`/reviews/`) of the dev environment in a browser, using "Reviews" in the left menu.
2. Observe: a table with the columns Location, Rating, Review text, Sentiment and Date, newest first, 20 reviews per page with Previous, Next and page numbers.
3. Observe what is missing: there is no way to choose a location, good or bad, or a week. The only way to find the bad reviews of a week is to read through every page.

## How to check it when built

1. Open the Reviews page and note the total number of reviews in the line under the table.
2. Choose "bad" and a week, for example the current week, and apply.
3. Compare the list with the real reviews of that week: only 1 and 2 stars, only written from Monday to Sunday of that week, newest first, and the number under the table matches.
4. Choose "good" instead and check that only 4 and 5 stars are shown. Choose "All ratings" and check that 3-star reviews appear again.
5. Choose a location (for example Airport) as well and check that only its reviews remain.
6. With a filter that matches more than 20 reviews, click "Next" and check that the filters are still chosen and that the second page continues the same list.
7. Choose a week in which nothing was written and check that "No reviews found" is shown.
8. Open the Dashboard and check that its numbers are the same as before and do not depend on what was chosen on the Reviews page.

## Expected result

Only reviews matching every chosen filter are shown, newest first, and their number matches the real data. "Good" shows only 4 and 5 stars, "bad" only 1 and 2 stars, and with no good or bad choice the 3-star reviews are included. The Dashboard is unchanged.

## Environment

To be checked on the dev environment first, then released to production.

## Attachments

Sketch of the Reviews page from the reporter.
