# Intent: review-topics

## Problem

ReviewRadar shows a score per location and lists every review, but a manager cannot see what customers talk about. To learn whether people complain about waiting, staff, prices or parking, they must read every review. The bad reviews of the demo data cluster on a few subjects (waiting, booking by phone, billing), and nothing in the app shows it.

## Goal

Every review is tagged with the topics it mentions, using a fixed list of seven topics and their keywords. A new Topics page shows, per topic, how many reviews mention it, how many of those are bad and their average rating, for all locations or one, over all time or the last 30 or 90 days. The Reviews page gets a Topic filter and shows the topics of each review. The location page and the monthly report get a short topics panel.

## Users

- Business owners and managers who are signed in.

## Out of scope

- Editing the topics or keywords in the app; they are fixed in the code (`reviews/topics.py`).
- Topics found by the Claude API, sentiment from the text, or other languages than English and Vietnamese.
- Storing topics on reviews: no migration. Topics are read from the stored search text.
- Topics in the Monthly report CSV, the Reviews CSV columns or the dashboard.
- A filter for "no topic" on the Reviews page.
