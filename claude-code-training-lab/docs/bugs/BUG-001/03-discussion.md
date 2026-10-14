# [BUG] Dashboard numbers look wrong: discussion

- **ID:** BUG-001
- **Reporter:** Maria, operations manager
- **Assignee:** not assigned yet
- **Note:** Simulated conversation for the Day 02 exercise. The replies were not written by the real reporter.

## Conversation

### 2026-10-14 · Assignee
Hi Maria, to fix the numbers before Friday we need a few details:

1. Which location was wrong, what did the dashboard show, and what did you calculate? (We found Riverside: screen shows 3, correct is 3.67. Is that the one?)
2. How should the average be displayed: 3.67 (two decimals), 3.7 (one decimal), or a whole number?
3. Is the number of reviews also wrong, or only the average score?
4. Please attach a screenshot of the dashboard and a photo or copy of your calculation.

### 2026-10-14 · Reporter (Maria)
1. It is Riverside. The Dashboard shows 3. I added up its ratings by hand: 4 + 5 + 2 = 11, and 11 ÷ 3 = 3.67.
2. One decimal is fine (3.7). The meeting slides use one decimal everywhere.
3. Only the average score is wrong. The number of reviews is correct for every location.
4. I saw it on the live system (production). I attached a screenshot of the Dashboard and a photo of my calculation.

### 2026-10-14 · Assignee
Thanks Maria. We reproduced it with the same data: Riverside shows 3 instead of 3.7. We will show every average with one decimal (Airport 2.0, Downtown 4.0, Riverside 3.7).

## Answers so far

| # | Question | Answer | Answered? |
|---|---|---|---|
| 1 | Which location was wrong, what did the dashboard show, and what did you calculate? (We found Riverside: screen shows 3, correct is 3.67. Is that the one?) | Riverside. The Dashboard shows 3; the hand calculation gives 3.67 (4 + 5 + 2 = 11, ÷ 3). Confirmed. | Yes |
| 2 | How should the average be displayed: 3.67 (two decimals), 3.7 (one decimal), or a whole number? | One decimal (3.7), as on the meeting slides. | Yes |
| 3 | Is the number of reviews also wrong, or only the average score? | Only the average score is wrong; the review counts are correct. | Yes |
| 4 | Please attach a screenshot of the dashboard and a photo or copy of your calculation. | Seen on production. Screenshot of the Dashboard and photo of the hand calculation sent. | Yes |

## Ready for the final issue?

- [x] Every question has an answer, or the reporter said it does not matter
- [x] New information from the conversation is reflected in the answers table
- [x] The steps can be followed by someone who was not in the conversation
