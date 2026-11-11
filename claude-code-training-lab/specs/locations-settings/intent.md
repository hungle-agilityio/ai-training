# Intent: locations-settings

## Problem

A business can only get a new location, or fix a location's name, through the Django admin or the demo seed. A clinic that opens a new branch, or renames one, cannot do it in ReviewRadar itself, and an empty installation tells the user to "add your first location" without saying where.

## Goal

Signed-in users add and rename locations on the Settings page. A new location shows everywhere locations show (dashboard, Reviews filter, goals, compare) with "No score" until it has reviews. Renaming keeps the location's reviews, goal and score. The empty dashboard links to the place where a location is added.

## Users

The owner and staff of a business, signed in to ReviewRadar. Everyone who is signed in may add and rename locations (the app has no roles).

## Out of scope

- Deleting or archiving a location (it would delete its reviews).
- Several businesses: a new location joins the one business; when none exists, the first location creates one named "My business".
- Address, opening hours or any field other than the name.
- A migration or a change to the demo data.
- Changes to the location page, the Reviews page, the reports, the compare page or the API other than showing the new or new name.
