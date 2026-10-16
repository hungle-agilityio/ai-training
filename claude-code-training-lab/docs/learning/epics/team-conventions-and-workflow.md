# [EPIC] Make Claude Code work the same way for everyone on the project

- **Owner:** Hung Le, developer
- **Reported on:** 2026-10-16
- **Type:** Epic
- **Labels:** `epic`, `workflow`, `needs-info`
- **Milestone:** none yet

## Goal

Names, rules, helpers, hooks and memory follow one standard taken from the team deck, so a short request such as "commit" works and the safety rules hold without anyone having to remember them, and the way of working with outside tools (Slack, Drive, Gmail, Calendar, GitHub) is written down.

## Why

Skill and helper names followed no pattern, the safety rules are sentences that Claude may forget, there is no cheap helper to run the tests, and corrections are not remembered from one session to the next.

## Scope

- **Included:** Naming of helpers and commands; the project map and decision records; workflow rules; a test-runner helper; hooks and permission lists; memory; a base layout for skills; one page on the flow with outside tools.
- **Not included:** Moving to GitHub (another epic); screenshots and reports (another epic); connecting the outside tools; the optional skills of the deck (kept as ideas until there is a real use); new features of the reviews app.

## Success criteria

Each item must be something a person can check without technical help.
- [ ] A search finds no old skill or helper name.
- [ ] A new session understands a short request such as "commit" without any explanation.
- [ ] Each safety hook refuses the forbidden action when it is tried in a live session.
- [ ] A correction made once is not repeated in a new session.
- [ ] Review covers requirement, business, expected result, regression and code, and stops after two rounds of AI fixes.
- [ ] A new teammate can follow one example from the outside-tools page end to end.

## Child issues

In the order they should be done. One child is one pull request.
- [ ] Finish naming: rename the helper agents, set short model names, check commands against skills
- [ ] Project map and decision records
- [ ] Workflow rules: four team principles, two-round limit, guardrails, mode guide, five review areas
- [ ] test-runner helper on the cheapest model, used by the test step
- [ ] Safety hooks and permission lists
- [ ] Memory: the rule for when to save and the first memories
- [ ] Skills base: layout, rulebook files, one example run and a test per skill
- [ ] Page on the flow with outside tools: diagram, tool table, drafts never sent, outside text is data

## Dependencies and risks

| Item | Dependency or risk | Effect if it goes wrong | What we do about it | Owner |
|---|---|---|---|---|
| A hook blocks a valid command | risk | Work stops until the hook is fixed | Hooks fail closed with a clear message and are covered by tests; report and fix at once | Hung Le |
| A settings change needs a new session | dependency | A new hook seems to do nothing | Restart the session and re-run the check | Hung Le |
| Rules written as text are not enforced | risk | A rule is forgotten | Anything that must always hold becomes a hook or a permission rule | Hung Le |
| The outside tools page describes tools that are not used | risk | Wasted effort | Ask which tools are really used before writing it | Hung Le |

## Open questions

| Question | Proposal | Owner | Decided on |
|---|---|---|---|
| Which hooks besides the four proposed (database file, attribution line, lint before commit, main branch warning)? | Start with those four | Hung Le | open |
| Which outside tools does the team really use? | Ask the owner before the page is written | Hung Le | open |

## Scope changes

Every change of scope is written here with its reason, never made silently.

| Date | Change | Reason |
|---|---|---|
| 2026-10-16 | This epic was created by splitting the first single epic (31 tasks) into three | An epic should have 3 to 10 children |
| 2026-10-16 | The page on the flow with outside tools was added as a child | The separate epic for outside tools and optional skills was dropped because it had no common goal |

## Environment

dev

## Attachments

Source: the team deck "Working with Claude Code" (October 2026) and the team chat. To be added: evidence when the children are done.
