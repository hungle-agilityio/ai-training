# [FEAT] Filter reviews by good or bad

- **Reporter:** Marcus, product owner
- **Reported on:** 2026-10-13
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`, `dashboard`

## Summary

Managers need a new **Reviews** page, reachable from the Dashboard, that lists individual reviews and lets them filter by good or bad and by week, to prepare the weekly meeting. Today no page lists individual reviews.

## Acceptance criteria

- When a manager opens the Reviews page, it lists the reviews of all locations, newest first. Each line shows the location, the stars, the review text and the date written.
- When a manager chooses a location in the location dropdown, only that location's reviews are shown.
- When a manager chooses "good", only reviews rated 4 or 5 stars are shown.
- When a manager chooses "bad", only reviews rated 1 or 2 stars are shown.
- Reviews rated 3 stars are shown only when no good/bad filter is chosen.
- When a manager chooses a week, only reviews written from Monday to Sunday of that week (Vietnam time, UTC+7) are shown.
- When a manager combines a location, a good/bad choice and a week, only reviews matching all of them are shown.
- The filters change only the list. The scores on the Dashboard do not change.
- When no review matches, the page shows "No reviews found" instead of an empty page.

## What exists today

1. Open the Dashboard page (`/dashboard/`) of the dev environment in a browser.
2. Observe: one line per location with its number of reviews and average score. There is no list of individual reviews and no filter.

## How to check it when built

1. Open the Dashboard, then follow the link to the Reviews page.
2. Choose "bad" and select the current week.
3. Compare the list with the real reviews of this week.

## Expected result

Only reviews rated 1 or 2 stars and written from Monday to Sunday of the chosen week are shown, newest first, and their number matches the real data. Choosing "good" shows only 4 and 5 stars. With no filter, 3-star reviews are included.

## Environment

To be checked on the dev environment first, then released to production.

## Attachments

Sketch of the Reviews page from the reporter.
