# [FEAT] Show which locations are getting better or worse

- **Reporter:** Marcus, product owner
- **Reported on:** 2026-10-22
- **Type:** New feature
- **Labels:** `feature`, `dashboard`, `needs-info`

## Summary

As a manager, I want to see on the Dashboard whether each location's score went up or down compared with the week before, so that I can step in early at a location that is getting worse instead of finding out from the monthly numbers. It changes the existing **Dashboard** page (`/dashboard/`) by adding a column to the Location scores table; it does not add a page.

## Scope

- A new "Trend" column in the Location scores table, after the Rating column.
- One trend per location, from the average rating of two Monday-to-Sunday weeks.

## Not in scope

- Charts or history over more than two weeks.
- Sending an alert by email or message when a location gets worse.
- Changing the existing score, the Status column or the "Need attention" box.
- The Reviews page.

## Acceptance criteria

Items marked (proposal) are not yet confirmed by the reporter.
- When a location has reviews in both of the last two full weeks, the screen must show in its Trend cell "Up" or "Down" with the difference between the two weekly averages, to one decimal, or "Same" when the difference is 0.0. (proposal)
- When the average of the last full week is lower than the week before by 0.5 or more, the screen must mark the Trend cell as a warning. (proposal)
- When a location has no reviews in one of the two weeks, the screen must show a dash in its Trend cell and no number.
- When there is nothing to show because there are no locations, the screen must keep showing "No locations yet" as today.
- When a location has no reviews at all, the screen must keep showing "No reviews yet" in its Rating cell and leave its Trend cell empty.
- When a manager reads the Rating and Status columns, the screen must show the same values as today, because the Trend does not change them.

## Scenarios

Today is Thursday 2026-10-22. The last full week is Monday 2026-10-12 to Sunday 2026-10-18 (Vietnam time). The week before is 2026-10-05 to 2026-10-11. Reviews of the current week, from Monday 2026-10-19, are not used.

**Scenario 1: a location gets worse**
- Given Riverside has these reviews: week of 2026-10-05: rated 4, 4, 5, 3, 4 (average 4.0); week of 2026-10-12: rated 3, 4, 2 (average 3.0)
- When the manager opens the Dashboard
- Then the Trend cell of Riverside shows "Down 1.0" and is marked as a warning

**Scenario 2: a location gets better**
- Given Airport has: week of 2026-10-05: rated 3, 4 (average 3.5); week of 2026-10-12: rated 4, 5 (average 4.5)
- When the manager opens the Dashboard
- Then the Trend cell of Airport shows "Up 1.0" and is not marked as a warning

**Scenario 3: not enough data**
- Given Newtown has reviews only in the week of 2026-10-12
- When the manager opens the Dashboard
- Then the Trend cell of Newtown shows a dash

**Scenario 4: a small drop**
- Given Harbour has: week of 2026-10-05: average 4.2; week of 2026-10-12: average 3.9
- When the manager opens the Dashboard
- Then the Trend cell of Harbour shows "Down 0.3" and is not marked as a warning, because the drop is smaller than 0.5

## Spec

- A week is Monday to Sunday in Vietnam time. A review written on Sunday at 23:59 belongs to that week; one written on the next Monday at 00:00 does not.
- The weekly average follows the existing score rule: one decimal, rounded half up (2.25 is 2.3). The difference is calculated from the two weekly averages as shown, for example 4.0 and 3.0 give 1.0.
- Texts: `Up 1.0`, `Down 1.0`, `Same`, and a dash for "not enough data". Numbers always have one decimal.
- Warning: the Trend cell is shown in the same warning style as "Needs attention" in the Status column.
- The last full week never includes the current week, so a trend does not change during the week.
- Column order of the table: Location, Reviews, Rating, Trend, Status.

## What exists today

1. Open the Dashboard (`/dashboard/`) of the dev environment.
2. Observe: the Location scores table has the columns Location, Reviews, Rating and Status. The Rating is the average of all reviews ever written, so a recent drop is hidden by old reviews.
3. Observe what is missing: there is no way to see whether a location is going up or down. The only way is to open the Reviews page, choose the location and a week, and compare by hand.

## How to check it when built

1. Open the Dashboard and find the Trend column between Rating and Status.
2. Choose a location with reviews in the last two full weeks. Open the Reviews page, choose that location and each of the two weeks, and calculate the two averages by hand.
3. Compare: the Trend must show the difference of the two averages with "Up" or "Down", to one decimal.
4. Find a location with reviews in only one of the two weeks and check that its Trend shows a dash.
5. Find a location that dropped by 0.5 or more and check that its Trend is marked as a warning.
6. Check that the Rating and Status of every location are the same as before the change.

## Expected result

Each location shows how its average rating of the last full week differs from the week before, with a warning when it dropped by 0.5 or more, a dash when a week has no reviews, and all existing numbers on the Dashboard unchanged.

## Open questions

1. Should the Trend compare the last two full weeks, or the current week so far against the last full week? Proposal: the last two full weeks, so the number does not move during the week. Owner: Marcus
2. How big must a drop be to count as "getting worse"? Proposal: 0.5 or more. Owner: Marcus
3. How many reviews must a week have before its average is trusted? A week with one review would show a big jump. Proposal: no minimum, but show the number of reviews of each week in a small hint when the manager points at the Trend cell. Owner: Marcus
4. Should the "Need attention" box at the top also count locations that are getting worse? Proposal: no, it keeps meaning "rated below 3.0". Owner: Marcus
5. Is a difference of 0.0 shown as "Same", or should small changes (under 0.1) also count as "Same"? Proposal: only 0.0 is "Same". Owner: Marcus

## Environment

To be checked on the dev environment first.

## Attachments

None yet.
