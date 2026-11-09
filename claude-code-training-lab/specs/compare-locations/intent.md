# Intent: compare-locations

## Problem

A business owner with several clinics wants to see how two of them stand next to each other: which one scores better, which gets more bad reviews, which replies faster, what customers talk about at each. Today the numbers are spread over the dashboard, two location pages and the Topics page, and must be read one by one.

## Goal

A page `/compare/` shows two chosen locations side by side for a period (all time, last 30 days, last 90 days): score, number of reviews, good and bad share, star breakdown, share of bad reviews replied in 24 hours, and the topics customers mention. The comparison can be downloaded as a CSV file.

## Users

The business owner and managers who are signed in (every page needs sign-in, as today).

## Out of scope

- More than two locations at once.
- A chart over time (the location page already has the weekly trend).
- Any change to the score, topic or reply-speed rules: the page reuses them.
- A migration or new demo data.
