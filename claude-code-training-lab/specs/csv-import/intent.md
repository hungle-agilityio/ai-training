# Intent: csv-import

## Problem

ReviewRadar only shows the demo reviews that `seed_demo_data` creates. A business that wants to try it with its own reviews has no way to bring them in, so the dashboard, the review list and the reports cannot show its real situation. Importing reviews is the first item of the MVP (`docs/app/reviewradar-project-context-2026-10.md`).

## Goal

A signed-in user uploads a CSV file of reviews on a new page, `/reviews/import/`. Good rows are saved as reviews of the matching locations, duplicates are skipped, and every bad row is listed with its row number and the reason. The file uses the same columns as the existing Export CSV, so an exported file can be imported again.

## Users

- Business owners and managers who are signed in, from the Reviews page.

## Out of scope

- Creating locations from the file: a row with an unknown location is an error.
- Undoing an import, an import history, or a preview step before saving.
- Other formats (Excel, JSON) or an API; importing replies.
- Date formats other than "YYYY-MM-DD HH:MM" and "YYYY-MM-DD".
- Keeping imported reviews on the live demo site: Render runs `seed_demo_data` on every start and the free plan keeps no disk, so imported reviews disappear when the site restarts. `../render.yaml` does not change.
- A migration: no field or table is added.
