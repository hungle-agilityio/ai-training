# [BUG] New location breaks the dashboard: analysis and questions

- **ID:** BUG-003
- **Reviewed on:** 2026-10-14
- **Status:** Waiting for reporter
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `crash`, `high-priority`, `reproduced`, `needs-info`, `env: dev`
- **Where:** The Dashboard page (`/dashboard/`) of the dev environment

## Analysis (3 sentences)

1. **What it asks:** The Dashboard must work again. Since a new location was added, it shows an error instead of the list, and Linh asked for it to be looked at on the day of the report (2026-10-13).
2. **What is ambiguous:** The report does not give the error message, the name of the new location, or whether that location already has reviews. It also does not say what the Dashboard should show for a location that has no reviews yet: hide it, show a score of 0, or show "no reviews yet".
3. **First step:** Add a location with no reviews and open the Dashboard (steps are in `04-final.md`). We reproduced the error this way: the whole page fails, so every location disappears, not only the new one. Then ask Linh what should be shown for a location without reviews.

## What we found so far

After adding a location with no reviews (Newtown), the whole Dashboard shows a server error (500) and lists no location at all, including the 3 that worked before.

## Questions for the reporter

1. What exact error text do you see on the screen? Please attach a screenshot.
2. Does the new location already have reviews? (We assume it has none.)
3. What should the Dashboard show for a location with no reviews: nothing, a score of 0, or "no reviews yet"?
