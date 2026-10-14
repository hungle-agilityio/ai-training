# [BUG] Dashboard numbers look wrong

- **Reporter:** Maria, operations manager
- **Reported on:** 2026-10-12
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `wrong-data`, `reproduced`, `env: production`, `deadline: 2026-10-16`

## Summary

The average score shown for each location on the Dashboard is wrong when the real average is not a whole number: Riverside shows 3 instead of 3.7. Every average must match the real average of the location's review ratings and be shown with one decimal. Maria needs this before Friday's review meeting (2026-10-16).

## Steps to reproduce

1. Open the Dashboard page (`/dashboard/`) in a browser. It lists three locations: Airport, Downtown and Riverside.
2. Find the line for **Riverside**. Read the number after `average_rating`.
3. Riverside has 3 reviews, rated 4, 5 and 2. Add them up (4 + 5 + 2 = 11) and divide by 3.
4. Compare your result with the number on the screen.

## Expected result

Every average is shown with one decimal:

| Location | Ratings of its reviews | Correct average |
|---|---|---|
| Airport | 2, 2, 3, 1 | 2.0 (8 ÷ 4) |
| Downtown | 5, 4, 3 | 4.0 (12 ÷ 3) |
| Riverside | 4, 5, 2 | 3.7 (11 ÷ 3 = 3.67, rounded to one decimal) |

## Actual result

Riverside shows `3`. Airport and Downtown look correct only because their real averages happen to be whole numbers. The number of reviews is correct for every location.
```
Airport:   review_count 4, average_rating 2
Downtown:  review_count 3, average_rating 4
Riverside: review_count 3, average_rating 3   <-- should be 3.7
```

## Environment

Seen by the reporter on production. Reproduced on the dev environment with the standard demo data.

## Attachments

Screenshot of the Dashboard showing Riverside's average as 3, and the reporter's hand calculation (4 + 5 + 2 = 11, 11 ÷ 3 = 3.67).
