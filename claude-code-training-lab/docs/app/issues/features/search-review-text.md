# [FEAT] Search reviews by the words in their text

- **Reporter:** Marcus, product owner
- **Reported on:** 2026-10-22
- **Type:** New feature
- **Labels:** `feature`, `reviews-list`, `needs-info`

## Summary

As a manager, I want to type a word into the Reviews page and see only the reviews that mention it, so that I can find out how many customers complain about the same thing, for example "waiting" or "parking". It changes the existing **Reviews** page (`/reviews/`) by adding a search box next to the existing filters; it does not add a page.

## Scope

- A "Search" box in the filter area of the Reviews page.
- The list, the count under the table and the page links follow the search.

## Not in scope

- Searching other pages.
- Showing the matched words in a different color.
- Saving a search or sending it as a report.
- Guessing words with spelling mistakes or similar meaning.

## Acceptance criteria

Items marked (proposal) are not yet confirmed by the reporter.
- When a manager types a word and clicks Apply, the screen must show only the reviews whose text contains that word, newest first.
- When a manager types a word in capital or small letters, the screen must find the same reviews regardless of the case. (proposal)
- When a manager types two or more words, the screen must show only the reviews that contain every one of the words, in any order. (proposal)
- When a manager types a search while a location, a rating or a week is also chosen, the screen must show only the reviews that match the search and every chosen filter.
- When a search is applied, the screen must show in the line under the table, for example "Showing 1-3 of 3 reviews", only the number of reviews that match.
- When a manager goes to another page of the results, the screen must keep the search, and when the manager changes the search, the screen must start again from the first page. (proposal)
- When no review matches, the screen must show "No reviews found" instead of an empty table, and when there are no reviews at all, it must keep showing "No reviews yet".
- When the search box is left empty or holds only spaces, the screen must show the list as if no search had been made.
- When a manager clicks Clear, the screen must empty the search box together with the other filters.

## Scenarios

**Scenario 1: one word**
- Given the system has 3 reviews that contain the word "parking": "No parking nearby" (Riverside, 2 stars), "Easy parking, friendly staff" (Airport, 5 stars) and "Parking was full" (Riverside, 3 stars), and 40 other reviews that do not
- When the manager types `parking` and clicks Apply
- Then 3 rows are shown, newest first, and the line under the table says "Showing 1-3 of 3 reviews"

**Scenario 2: case does not matter**
- Given the same data
- When the manager types `PARKING` and clicks Apply
- Then the same 3 rows are shown

**Scenario 3: two words**
- Given the same data
- When the manager types `parking full` and clicks Apply
- Then only "Parking was full" is shown

**Scenario 4: search with a filter**
- Given the same data
- When the manager types `parking`, chooses the location Riverside and clicks Apply
- Then only the two Riverside reviews are shown

**Scenario 5: no match**
- Given the same data
- When the manager types `elevator` and clicks Apply
- Then the screen shows "No reviews found" and no table

## Spec

- The search looks at the complete review text, not only the shortened text shown in the table.
- A "word" is any part of the text, so `park` also finds "parking". (proposal)
- Capital and small letters are the same. Letters with accents are different from letters without accents: `dau` does not find "đau". (proposal)
- Leading and trailing spaces are removed before searching. Several spaces between words count as one.
- The search box is labelled "Search" and has the hint "Words in the review". It is the first field of the filter area.
- Texts: "No reviews found" (nothing matches), "No reviews yet" (no reviews at all), "Showing 1-3 of 3 reviews" (the count).
- The Dashboard and the Sentiment column do not change.

## What exists today

1. Open the Reviews page (`/reviews/`) of the dev environment, using "Reviews" in the left menu.
2. Observe: filters for location, rating and week, and a table with the columns Location, Rating, Review text, Sentiment and Date, 20 reviews per page.
3. Observe what is missing: there is no way to look for a word. The only way is to read every page.

## How to check it when built

1. Open the Reviews page and note the total number of reviews under the table.
2. Type `parking` in the Search box and click Apply. Check that every row shown contains "parking" in its text, and that the number under the table matches the number of rows over all pages.
3. Type `PARKING` and check that the same rows appear.
4. Type `parking full` and check that only reviews with both words remain.
5. Choose the location Riverside as well and check that only Riverside reviews remain.
6. With a search that matches more than 20 reviews, click "Next" and check that the search is still in the box and that page 2 continues the same list.
7. Type `elevator` (a word nobody wrote) and check that "No reviews found" is shown. Click Clear and check that the box is empty and the full list is back.

## Expected result

Only reviews whose text contains every typed word, and that also match every chosen filter, are shown, newest first, and their number under the table matches the real data.

## Open questions

1. Must all typed words be in the review, or any one of them? Proposal: all of them. Owner: Marcus
2. Should a search for `dau` also find "đau" (accents ignored)? Customers often write without accents. Proposal: no for now; accents are different. Owner: Marcus
3. Should `park` find "parking" (part of a word), or only whole words? Proposal: part of a word. Owner: Marcus
4. Is there a shortest search? A one-letter search would match almost everything. Proposal: no minimum. Owner: Marcus
5. The Reviews page already has filters for location, rating and week. Should the search be reset by the Clear button together with them? Proposal: yes. Owner: Marcus

## Environment

To be checked on the dev environment first.

## Attachments

None yet.
