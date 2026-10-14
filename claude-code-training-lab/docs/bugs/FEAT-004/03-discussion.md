# [FEAT] Filter reviews by good or bad: discussion

- **ID:** FEAT-004
- **Reporter:** Marcus, product owner
- **Assignee:** not assigned yet
- **Note:** Simulated conversation for the Day 02 exercise. The replies were not written by the real reporter.

## Conversation

### 2026-10-14 · Assignee
Hi Marcus, before we build the filters we need a few decisions:

1. What is a good review and what is a bad one? Our proposal: 4-5 stars good, 1-2 stars bad, 3 stars neutral (visible only when no filter is chosen). Or should it use the automatic sentiment instead?
2. What is a week: Monday to Sunday of a week the manager picks, or the last 7 days? In which time zone?
3. Where should it be: a new "Reviews" page, or filters on the existing Dashboard? For one location, all locations, or both?
4. Can the filters be combined (for example bad reviews of last week)? Should the filter also change the scores on the Dashboard, or only the list?
5. What should each review line show (location, stars, text, date)? Do you have a sketch?

### 2026-10-14 · Reporter (Marcus)
1. Your proposal is fine: 4-5 stars good, 1-2 stars bad, 3 stars neutral. Use the star rating, not the automatic sentiment.
2. A week is Monday to Sunday, and the manager picks which week. Use Vietnam time (UTC+7).
3. A new "Reviews" page, reachable from the Dashboard. It shows all locations by default, with a dropdown to choose one location.
4. Yes, the filters can be combined. They change only the list, not the scores on the Dashboard.
5. Each line shows the location, the stars, the review text and the date written, newest first. I attached a sketch.

### 2026-10-14 · Assignee
Thanks Marcus. We will write these as acceptance criteria. Reviews rated 3 stars appear only when no good/bad filter is chosen.

## Answers so far

| # | Question | Answer | Answered? |
|---|---|---|---|
| 1 | What is a good review and what is a bad one? Our proposal: 4-5 stars good, 1-2 stars bad, 3 stars neutral (visible only when no filter is chosen). Or should it use the automatic sentiment instead? | Accepted: 4-5 stars good, 1-2 stars bad, 3 stars neutral (shown only with no good/bad filter). Star rating, not automatic sentiment. | Yes |
| 2 | What is a week: Monday to Sunday of a week the manager picks, or the last 7 days? In which time zone? | Monday to Sunday of a week the manager picks; Vietnam time (UTC+7). | Yes |
| 3 | Where should it be: a new "Reviews" page, or filters on the existing Dashboard? For one location, all locations, or both? | A new "Reviews" page reachable from the Dashboard; all locations by default, dropdown to choose one. | Yes |
| 4 | Can the filters be combined (for example bad reviews of last week)? Should the filter also change the scores on the Dashboard, or only the list? | Filters can be combined; they change only the list, not the Dashboard scores. | Yes |
| 5 | What should each review line show (location, stars, text, date)? Do you have a sketch? | Each line: location, stars, review text, date written; newest first. Sketch sent. | Yes |

## Ready for the final issue?

- [x] Every question has an answer, or the reporter said it does not matter
- [x] New information from the conversation is reflected in the answers table
- [x] The steps can be followed by someone who was not in the conversation
