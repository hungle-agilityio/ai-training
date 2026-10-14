# [BUG] New location breaks the dashboard: discussion

- **ID:** 3
- **Reporter:** Linh, branch coordinator
- **Assignee:** not assigned yet
- **Note:** Simulated conversation for the Day 02 exercise. The replies were not written by the real reporter.

## Conversation

### 2026-10-14 · Assignee
Hi Linh, to fix the Dashboard error we need a few details:

1. What exact error text do you see on the screen? Please attach a screenshot.
2. Does the new location already have reviews? (We assume it has none.)
3. What should the Dashboard show for a location with no reviews: nothing, a score of 0, or "no reviews yet"?

### 2026-10-14 · Reporter (Linh)
1. The page shows "Server Error (500)" and nothing else. I attached a screenshot.
2. The new location is called Newtown. It was created yesterday and has no reviews yet.
3. I would like to still see Newtown in the list, with "No reviews yet" instead of a score.

### 2026-10-14 · Assignee
Thanks Linh. We reproduced the error by adding a location without reviews. We will show such a location with 0 reviews and "No reviews yet" instead of a score, and keep the other locations visible.

## Answers so far

| # | Question | Answer | Answered? |
|---|---|---|---|
| 1 | What exact error text do you see on the screen? Please attach a screenshot. | Page shows "Server Error (500)" and nothing else. Screenshot sent. | Yes |
| 2 | Does the new location already have reviews? (We assume it has none.) | The new location is Newtown, created yesterday, with no reviews yet. Confirmed. | Yes |
| 3 | What should the Dashboard show for a location with no reviews: nothing, a score of 0, or "no reviews yet"? | Show Newtown in the list with "No reviews yet" instead of a score. | Yes |

## Ready for the final issue?

- [x] Every question has an answer, or the reporter said it does not matter
- [x] New information from the conversation is reflected in the answers table
- [x] The steps can be followed by someone who was not in the conversation
