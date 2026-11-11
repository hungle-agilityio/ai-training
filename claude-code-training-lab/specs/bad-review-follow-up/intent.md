# Intent: bad-review-follow-up

## Problem

A bad review (1 to 2 stars) usually needs more than a public reply: someone calls the customer, offers a new visit, or talks to the team. Today ReviewRadar only knows whether a review has a reply. Nobody can see which unhappy customers were contacted and which problems are solved, so cases are forgotten or handled twice.

## Goal

Every bad review is a follow-up case with a status: Open, Contacted or Resolved, and a short internal note. A bad review nobody touched is Open. Staff change the status and the note on the review's reply page. The Reviews page shows the status of each bad review and filters by it, and the dashboard says how many cases are still open, with a link to them.

## Users

The owner and staff of a business, signed in to ReviewRadar. Everyone who is signed in may change a case (the app has no roles).

## Out of scope

- Cases for 3 to 5 star reviews.
- A history of every change; only the current status, note, who changed it last and when.
- Changing the status automatically when a reply is saved.
- Alerts or e-mails about open cases.
- The status in the CSV export columns, the location page, the Reply drafts page, the reports, the compare page or the dashboard API (`/api/dashboard/`).
- A data migration: bad reviews without a stored case are Open.
