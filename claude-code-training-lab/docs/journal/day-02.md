# Day 2

## What I did

- Analysed 5 seeded tickets: three-sentence analysis and questions for the reporter.
- Reproduced bugs #1, #2 and #3 and wrote their failing tests. #5 cannot be reproduced (the feature does not exist).
- Built ticket tooling: templates, `write-ticket` and `git` skills, `ticket-analyst` and `ticket-planner` agents, rules in `CLAUDE.md`.
- Extra: HTML dashboard, reviews page (#6), fixed bug #1.

## What I learned

- A good bug report: exact page, values, steps that are only user actions, expected vs actual.
- Verify hypotheses by running them (N+1 hides on SQLite until query delay is added).
- A failing test is the best repro.
- Traps: `round()` is half-even, `//` returns an int, `get_page(0)` returns the last page.

## Blockers

- 
