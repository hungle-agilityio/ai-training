# [BUG] Dashboard is very slow: discussion

- **ID:** 2
- **Reporter:** Tom, regional director
- **Assignee:** not assigned yet
- **Note:** Simulated conversation for the Day 02 exercise. The replies were not written by the real reporter.

## Conversation

### 2026-10-14 · Assignee
Hi Tom, to find out why the Dashboard is slow we need a few details:

1. Roughly how many locations and how many reviews are loaded?
2. How many seconds does the Dashboard take to open? Is it slow every time or only the first time?
3. Which website address do you open (production or a test site)? Which browser?
4. How fast should it be for you to be happy (for example under 2 seconds)?
5. Please send a short screen recording of the page loading.

### 2026-10-14 · Reporter (Tom)
1. About 500 locations, with 3 to 4 reviews each (roughly 1,800 reviews in total).
2. About 25 seconds, every time I open it, not only the first time.
3. The live system (production), in Chrome on a laptop with office Wi-Fi.
4. Under 2 seconds would be fine.
5. I attached a screen recording. The page stays white for about 25 seconds, then the whole list appears at once.

### 2026-10-14 · Assignee
Thanks Tom. With 500 locations on our dev environment the page opens in about 0.1 second, so the delay only shows on production. We will use 2 seconds as the target.

## Answers so far

| # | Question | Answer | Answered? |
|---|---|---|---|
| 1 | Roughly how many locations and how many reviews are loaded? | About 500 locations, 3 to 4 reviews each (about 1,800 reviews). | Yes |
| 2 | How many seconds does the Dashboard take to open? Is it slow every time or only the first time? | About 25 seconds, every time. | Yes |
| 3 | Which website address do you open (production or a test site)? Which browser? | Production, Chrome, office Wi-Fi. | Yes |
| 4 | How fast should it be for you to be happy (for example under 2 seconds)? | Under 2 seconds. | Yes |
| 5 | Please send a short screen recording of the page loading. | Screen recording sent: white page for about 25 seconds, then the whole list appears. | Yes |

## Ready for the final issue?

- [x] Every question has an answer, or the reporter said it does not matter
- [x] New information from the conversation is reflected in the answers table
- [x] The steps can be followed by someone who was not in the conversation
