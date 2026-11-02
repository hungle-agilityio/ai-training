# Intent: location-page

## Problem

ReviewRadar shows every location in one dashboard table and every review in one list. A manager who wants to know how one location is doing has no page for it: there is no rating breakdown per location, and no way to see whether its score is getting better or worse week by week. "Trend per branch" is still missing from the MVP (`docs/app/reviewradar-project-context-2026-10.md`).

## Goal

Each location has its own page at `/locations/<id>/` with its score, its rating breakdown, a chart of its average rating per week for the last 8 weeks, and its 5 newest reviews. The dashboard and the review list link to it. The page goes live on Render at the release after the whole epic is merged.

## Users

- Business staff and owners who are signed in (every signed-in user sees every location, as today).

## Out of scope

- A list page of all locations, or a new sidebar item: the page is reached through links.
- Editing a location, or anything that writes data.
- A JSON or CSV export of the location page or of the trend.
- A JavaScript chart library; trends by month or year; comparing locations on one chart.
- Changing where the dashboard's location name links to (it keeps opening the filtered review list).
