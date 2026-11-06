# Intent: reply-speed

## Problem

Staff can now reply to reviews (epic #236), but nobody can see how fast they do it. An unhappy customer who waits days for an answer is often a lost customer, and the owner of several locations has no number that shows which location answers bad reviews quickly and which one lets them sit.

## Goal

The dashboard shows, for all locations together and for each location, the share of bad reviews (1 to 2 stars) that got a reply within 24 hours, and the average time to the first reply. The demo data has realistic reply times so the numbers mean something on the live site.

## Users

- Business owners and managers who are signed in, on `/dashboard/`.

## Out of scope

- Alerts or e-mails about late replies (a separate feature).
- A time filter (last 30 days, this month): the numbers cover all reviews, like the other dashboard numbers.
- Reply speed of good or neutral reviews, business hours, or a target other than 24 hours.
- The location page, the reports page and the dashboard API (`/api/dashboard/`) do not change.
- A migration: the reply time comes from the dates already stored.
