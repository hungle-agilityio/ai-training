# [BUG] Reply drafts come out in the wrong language: discussion

- **ID:** 5
- **Reporter:** Hana, QA
- **Assignee:** not assigned yet
- **Note:** Simulated conversation for the Day 02 exercise. The replies were not written by the real reporter.

## Conversation

### 2026-10-14 · Assignee
Hi Hana, to find the cause we need a few details about the wrong-language replies:

1. Where did you see the draft replies (which page or screen, what address)? Which version of the app and which environment (test or production)?
2. For each wrong case, please send: the review text, the language you expected, the reply you got, the time, and a screenshot.
3. About how many drafts did you try, and how many were wrong (for example 3 out of 20)?
4. Which languages were involved? Were some reviews very short or written in two languages?
5. If you ask for a draft for the same review again, is the result always wrong, or does it change?

### 2026-10-14 · Reporter (Hana)
1. I tested on staging, on the review detail page, with the "Suggest reply" button.
2. Three examples: (a) the review "Nhân viên rất thân thiện nhưng phải chờ lâu." (Vietnamese) got an English reply; (b) "Très bon service, merci !" (French) got an English reply; (c) "Great doctor, but chờ lâu quá" (English mixed with Vietnamese) got a Vietnamese reply. Screenshots attached.
3. I tried 20 reviews and 6 replies were wrong.
4. Languages were English, Vietnamese and French. All 6 wrong replies were for Vietnamese or French reviews, or the mixed one. English reviews were always answered correctly.
5. It changes: if I click "Suggest reply" again on the same review, I sometimes get the right language and sometimes not.

### 2026-10-14 · Assignee
Thanks Hana. This is enough for steps to reproduce. We could not find the feature on our dev environment, so it will be checked on staging first.

## Answers so far

| # | Question | Answer | Answered? |
|---|---|---|---|
| 1 | Where did you see the draft replies (which page or screen, what address)? Which version of the app and which environment (test or production)? | Staging, review detail page, "Suggest reply" button. | Yes |
| 2 | For each wrong case, please send: the review text, the language you expected, the reply you got, the time, and a screenshot. | (a) Vietnamese review got an English reply; (b) French review got an English reply; (c) mixed English/Vietnamese review got a Vietnamese reply. Screenshots sent. | Yes |
| 3 | About how many drafts did you try, and how many were wrong (for example 3 out of 20)? | 20 reviews tried, 6 replies wrong. | Yes |
| 4 | Which languages were involved? Were some reviews very short or written in two languages? | English, Vietnamese, French. All wrong replies were for non-English or mixed reviews; English reviews were always right. | Yes |
| 5 | If you ask for a draft for the same review again, is the result always wrong, or does it change? | Changes between attempts on the same review (sometimes right, sometimes wrong). | Yes |

## Ready for the final issue?

- [x] Every question has an answer, or the reporter said it does not matter
- [x] New information from the conversation is reflected in the answers table
- [x] The steps can be followed by someone who was not in the conversation
