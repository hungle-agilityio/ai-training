# [BUG] Dashboard numbers look wrong

- **Reporter:** Maria, operations manager
- **Reported on:** 2026-10-12
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `wrong-data`, `reproduced`, `env: production`, `deadline: 2026-10-16`

## Summary

On the Dashboard page, the average score of a location is wrong whenever the real average is not a whole number: Riverside shows 3.0 instead of 3.7. Every location average must match the real average of its review ratings, shown with one decimal and rounded half up (2.25 shows as 2.3, like a hand calculation or Excel). The colour label and the stars next to the score must follow the same number. Maria needs this before Friday's review meeting (2026-10-16). The same wrong numbers also appear in the data export (the "Export JSON" button).

## Steps to reproduce

1. Open the Dashboard page (`/dashboard/`) of the dev environment in a browser.
2. In the "Location scores" table, find the line for **Riverside** and read the number in the "Rating" column. The table lists Airport, Downtown and Riverside.
3. Riverside has 3 reviews, rated 4, 5 and 2. Add them up (4 + 5 + 2 = 11) and divide by 3.
4. Compare your result with the number in the table.
5. Click "Export JSON" and compare Riverside's average in the export too.

## Expected result

Every location shows its real average with one decimal:

| Location | Ratings of its reviews | Correct average |
|---|---|---|
| Airport | 2, 2, 3, 1 | 2.0 (8 ÷ 4) |
| Downtown | 5, 4, 3 | 4.0 (12 ÷ 3) |
| Riverside | 4, 5, 2 | 3.7 (11 ÷ 3 = 3.67, rounded to one decimal) |

- The stars next to Riverside's score are filled to about 74% (3.7 out of 5).
- The label next to the score follows the score shown on screen. For example, an average of 2.96 is shown as 3.0 and is labelled "Watch", not "Needs attention".
- The data export shows 3.7 for Riverside.

## Actual result

Riverside shows **3.0** in the table, and the data export shows 3. Airport (2.0) and Downtown (4.0) look correct only because their real averages happen to be whole numbers. The stars next to Riverside are filled to only 60% instead of about 74%. The number of reviews is correct for every location.

The "Average rating" box at the top of the page (3.1 out of 5) is **correct**: it is the average of all 10 reviews (31 stars ÷ 10), not the average of the three locations.

## Environment

Seen by the reporter on production. Reproduced on the dev environment with the standard demo data.

## Attachments

Screenshot of the Dashboard showing Riverside's average as 3.0, and the reporter's hand calculation (4 + 5 + 2 = 11, 11 ÷ 3 = 3.67).
