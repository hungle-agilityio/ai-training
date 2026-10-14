# [BUG] Dashboard is very slow: analysis and questions

- **ID:** BUG-002
- **Reviewed on:** 2026-10-14
- **Status:** Waiting for reporter
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `performance`, `partly-reproduced`, `needs-info`, `env: dev`
- **Where:** The Dashboard page (`/dashboard/`) of the dev environment

## Analysis (3 sentences)

1. **What it asks:** The Dashboard must open quickly again when all of Tom's locations are loaded, like it did in the demo with only a few locations.
2. **What is ambiguous:** "Takes forever" has no number. We don't know how many locations and reviews Tom has, how many seconds the page takes, whether it is slow every time or only the first time, or which website address and computer he uses. We also have no target (for example "under 2 seconds") to decide when it is fixed.
3. **First step:** Load a large number of locations and measure how much work the Dashboard does for one visit (steps are in `04-final.md`), then ask Tom the questions below. We found that the work grows with every location added: 3 locations cause 4 data lookups, and 503 locations cause 504 (one extra lookup per location). That is why a few locations feel instant and many feel slow.

## What we found so far

With the 3 standard demo locations the Dashboard does 4 data lookups; with 503 locations it does 504 (one extra lookup per location). On the dev environment the page still opens in about 0.1 second, so we cannot see the delay yet.

## Questions for the reporter

1. Roughly how many locations and how many reviews are loaded?
2. How many seconds does the Dashboard take to open? Is it slow every time or only the first time?
3. Which website address do you open (production or a test site)? Which browser?
4. How fast should it be for you to be happy (for example under 2 seconds)?
5. Please send a short screen recording of the page loading.
