# [FEAT] Reviews page to show all reviews

- **Reporter:** Hung Le
- **Reported on:** 2026-10-14
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`, `needs-info`

## Summary

Users need a new **Reviews** page that shows every review in a table, split into pages, with tooltips (small text boxes shown on hover) where they help. This is a completely new page. Today no page lists all reviews: the Dashboard only shows the 6 most recent ones, and the "Reviews" item in the left menu is greyed out with the tag "Soon". Filters (good or bad, by week) are not part of this ticket; ticket #4 adds them on top of this page.

## Acceptance criteria

All items are (proposal) until the reporter confirms them.
- When a user clicks "Reviews" in the left menu, the Reviews page opens. (proposal)
- The page shows a table with the columns Location, Rating (stars), Review text, Sentiment (Positive, Neutral or Negative, from the stars) and Date. (proposal)
- Reviews are shown newest first. (proposal)
- Each page shows 20 reviews. Under the table, the user sees Previous, Next and page numbers, and a line such as "Showing 1-20 of 1,810 reviews". (proposal)
- When the user chooses another page, the table shows the reviews of that page. On the first page "Previous" is disabled, and on the last page "Next" is disabled. (proposal)
- A review text longer than 120 characters is shortened with "…". Hovering over it shows the full text. (proposal)
- Hovering over the stars shows the rating, for example "4 out of 5". (proposal)
- Dates are shown like "Oct 14, 2026" in Vietnam time (UTC+7). (proposal)
- When there are no reviews, the page shows "No reviews yet" instead of an empty table. (proposal)
- On a narrow screen such as a phone, the table scrolls sideways. (proposal)
- With about 1,800 reviews, the page opens in under 2 seconds. (proposal)

## What exists today

1. Open the Dashboard page (`/dashboard/`) of the dev environment in a browser.
2. In the left menu, "Reviews" is greyed out with the tag "Soon" and cannot be clicked.
3. The "Latest reviews" panel shows only the 6 most recent reviews. There is no way to see the others.

## How to check it when built

1. Open the Dashboard page and click "Reviews" in the left menu.
2. Check that the table lists the 20 newest reviews, with the columns Location, Rating, Review text, Sentiment and Date.
3. Click "Next" and check that the next 20 reviews appear and that the line under the table changes to "Showing 21-40 ...".
4. Click "Previous" until you are back on the first page and check that "Previous" is disabled.
5. Hover over a shortened review text and check that the full text appears.
6. Hover over the stars of a review rated 4 and check that "4 out of 5" appears.

## Expected result

Every review is reachable through the pages, newest first. The number of reviews in the line under the table matches the real number of reviews. (proposal)

## Environment

Not decided yet (dev, staging or production to be confirmed).

## Attachments

Sketch or example of the page from the reporter (to be added).
