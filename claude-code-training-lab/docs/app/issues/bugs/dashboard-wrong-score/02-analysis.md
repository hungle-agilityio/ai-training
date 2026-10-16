# [BUG] Dashboard numbers look wrong: analysis and questions

- **ID:** 1
- **Reviewed on:** 2026-10-14
- **Status:** Waiting for reporter
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `wrong-data`, `reproduced`, `needs-info`, `env: dev`, `deadline: 2026-10-16`
- **Where:** The Dashboard page (`/dashboard/`) of the dev environment (the page that lists every location with its review count and average score)

## Analysis (3 sentences)

1. **What it asks:** The average score shown for each location on the Dashboard must match the real average of that location's review ratings. Maria needs this fixed before Friday's review meeting (2026-10-16).
2. **What is ambiguous:** The report does not say which location looked wrong, which number was wrong (average score or number of reviews), what the dashboard showed, or what Maria calculated by hand. It also does not say how the average should be written: 3.67, 3.7, or a whole number. We found one wrong location in the standard demo data (Riverside), but we need Maria to confirm it is the same one and to choose the format.
3. **First step:** Open the Dashboard, calculate each location's average by hand from its ratings, and compare with the screen (steps are in `04-final.md`). Riverside shows 3 instead of 3.67, so the fix is to show the exact average. Then confirm the display format with Maria.

## What we found so far

Riverside (ratings 4, 5, 2) shows an average of 3 on the Dashboard; the correct average is 3.67 (11 ÷ 3). Airport and Downtown look right only because their real averages are whole numbers (2 and 4).

## Questions for the reporter

1. Which location was wrong, what did the dashboard show, and what did you calculate? (We found Riverside: screen shows 3, correct is 3.67. Is that the one?)
2. How should the average be displayed: 3.67 (two decimals), 3.7 (one decimal), or a whole number?
3. Is the number of reviews also wrong, or only the average score?
4. Please attach a screenshot of the dashboard and a photo or copy of your calculation.
