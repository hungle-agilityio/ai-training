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
- A short message when the typed text is too short to search.

## Not in scope

- Searching other pages.
- Showing the matched words in a different color.
- Saving a search or sending it as a report.
- Guessing words with spelling mistakes or similar meaning.
- Ignoring accents, so `dau` does not find "đau".
- Matching whole words only.

## Acceptance criteria

Items marked (proposal) are not yet confirmed by the reporter.
- When a manager types a word and clicks Apply, the screen must show only the reviews whose text contains that word, newest first.
- When a manager types a word in capital or small letters, the screen must find the same reviews regardless of the case, for every letter, including letters with accents (`NHÂN` finds "Nhân").
- When a manager types two or more words, the screen must show only the reviews that contain every one of the words, in any order.
- When a manager types a search while a location, a rating or a week is also chosen, the screen must show only the reviews that match the search and every chosen filter.
- When a search is applied, the screen must show in the line under the table, for example "Showing 1-3 of 3 reviews", only the number of reviews that match.
- When a manager goes to another page of the results, the screen must keep the search, and when the manager changes the search, the screen must start again from the first page. (proposal)
- When no review matches, the screen must show "No reviews found" instead of an empty table, and when there are no reviews at all, it must keep showing "No reviews yet".
- When the search box is left empty or holds only spaces, the screen must show the list as if no search had been made, without any message.
- When the typed text has fewer than 3 characters (leading and trailing spaces not counted), the screen must show the message "Type at least 3 characters to search." and must not filter by the search, while the other chosen filters still apply.
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

**Scenario 6: too short**
- Given the same data
- When the manager types `pa` and clicks Apply
- Then the screen shows the message "Type at least 3 characters to search." and the list as if there were no search

**Scenario 7: letters with accents**
- Given a review "Đau chân đỡ hẳn, nhân viên thân thiện" and a review "Dau dau khi cho doi"
- When the manager types `ĐAU CHÂN` and clicks Apply
- Then only the first review is shown, and `dau` alone does not show the first review

## Spec

- The search looks at the complete review text, not only the shortened text shown in the table.
- A search finds any part of the text, so `park` also finds "parking".
- Capital and small letters are the same for every letter, including letters with accents: `ĐAU`, `Đau` and `đau` give the same result, and so do `NHÂN` and `nhân`.
- Letters with accents are different from letters without accents: `dau` does not find "đau".
- Leading and trailing spaces are removed before searching. Several spaces between words count as one.
- The shortest search is 3 characters, counted on the whole typed text after the spaces are removed (`an to` has 5). A shorter text shows the message `Type at least 3 characters to search.` under the Search box and is not used to filter.
- A search is a search for text, not a pattern: characters such as `%` and `_` are searched as they are typed.
- The typed search is part of the page address, like the other filters, so the next and previous page keep it.
- The typed search can be a customer's name or phone number, so it must never be written to the logs.
- The search box is labelled "Search" and has the hint "Words in the review". It is the first field of the filter area.
- Texts: "No reviews found" (nothing matches), "No reviews yet" (no reviews at all), "Showing 1-3 of 3 reviews" (the count), "Type at least 3 characters to search." (too short).
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
8. Type `pa` and check that the message "Type at least 3 characters to search." appears and the list is not filtered.
9. Type a Vietnamese word in capital letters with accents (for example `NHÂN`) and check that reviews with "nhân" or "Nhân" are found; then type it without accents (`nhan`) and check that they are not.
10. Type `100%` and check that it is searched as typed and does not match everything.

## Expected result

Only reviews whose text contains every typed word, and that also match every chosen filter, are shown, newest first, and their number under the table matches the real data.

## Open questions

These are assumptions that nobody has vetoed yet. Marcus confirms or changes them.
1. Is there a longest search? Assumption: 100 characters; anything longer is cut to the first 100. Owner: Marcus

## Environment

To be checked on the dev environment first.

## Attachments

None yet.
