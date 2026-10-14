# [BUG] New location breaks the dashboard

- **Reporter:** Linh, branch coordinator
- **Reported on:** 2026-10-13
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `crash`, `high-priority`, `reproduced`, `env: production`

## Summary

Since a new location (Newtown) with no reviews was added, the whole Dashboard shows "Server Error (500)" and no location is listed. The Dashboard must work again and show Newtown with 0 reviews and "No reviews yet" instead of a score.

## Steps to reproduce

1. Add a new location called **Newtown** next to the 3 existing ones (Airport, Downtown, Riverside), and make sure it has no reviews. On the test environment, you can also get this situation by deleting all reviews of Newtown.
2. Open the Dashboard page (`/dashboard/`) in a browser.
3. Observe the result: the page shows an error instead of the numbers, because it cannot calculate an average score for a location that has no reviews.

## Expected result

The page opens and lists all 4 locations. Newtown appears with 0 reviews and "No reviews yet" instead of a score. The other 3 locations are unchanged.

## Actual result

The page shows "Server Error (500)" and nothing else. No location is listed at all, including the 3 that worked before.

## Environment

Seen by the reporter on production. Reproduced on the dev environment.

## Attachments

Screenshot of the error page from the reporter.
