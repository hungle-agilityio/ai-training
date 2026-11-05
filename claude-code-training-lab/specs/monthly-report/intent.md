# Intent: monthly-report

## Problem

ReviewRadar shows the score of each location for all time (dashboard) and week by week for one location (location page). A business owner who reviews the month, or reports to a client, cannot see one month for every location side by side, cannot tell whether a location did better or worse than the month before, and has no file to send. On Render the demo reviews are all from the last 5 days, so anything per month shows almost nothing there.

## Goal

A new page `/reports/` shows, for a chosen month (Vietnam time), every location's review count, average score, good and bad reviews, and the change of the average against the previous month, with a CSV download of the same table. "Reports" appears in the sidebar. The demo reviews spread over the last 3 months so the page has something to show on Render. It goes live at one release after the whole epic is merged.

## Users

- Business staff and owners who are signed in (every signed-in user sees every location, as today).

## Out of scope

- A total row for all locations, charts, a year view, a free date range or any month older than 12 months.
- Writing data, a migration, or new demo reviews (the 14 demo reviews stay; only their dates move).
- E-mailing or scheduling the report.
- Changing the dashboard, the location page or the Reviews page.
