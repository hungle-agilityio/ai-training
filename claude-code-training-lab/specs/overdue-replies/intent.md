# Intent: overdue-replies

## Problem

The dashboard shows how many reviews still need a reply and how many bad reviews got one within 24 hours, and the Reply drafts page lists every review without a reply. But nobody can see at a glance which bad reviews have already waited too long. An unhappy customer who has waited more than a day is the one most likely to be lost, and today that review looks the same as one written an hour ago.

## Goal

A bad review (1 to 2 stars) with no reply after 24 hours is "overdue". The Reply drafts page marks those reviews and can show only them, and the dashboard says how many there are, with a link to that list. The rule is the one already used by "Replied in 24h", so the numbers agree.

## Users

- Business owners and managers who are signed in, on `/dashboard/` and `/replies/`.

## Out of scope

- Alerts or e-mails about overdue reviews.
- A count on the sidebar or on the "Overdue only" tab (it would add a query to the page).
- Overdue for 3 to 5 star reviews, business hours, or a limit other than 24 hours.
- The location page, the reports page, the Reviews page and the dashboard API (`/api/dashboard/`) do not change.
- A migration or a change to the demo data.
