# [EPIC] Prove every change with evidence: browser check, reports and pull request drafts

- **Owner:** Hung Le, developer
- **Reported on:** 2026-10-16
- **Type:** Epic
- **Labels:** `epic`, `evidence`, `needs-info`
- **Milestone:** none yet

## Goal

Every change that people can see comes with a report that opens by itself after verify, with before and after screenshots and sensitive data masked, and with a pull request draft that carries the evidence.

## Why

Today verify only says "check it in the running app". Reviewers cannot see a change without running it, and a long answer in the terminal is lost.

## Scope

- **Included:** A browser check in verify; the report as a local file; sharing it as a private link; before and after screenshots; masking of sensitive data; the pull request draft.
- **Not included:** Client documents (Word or slides); a full browser test suite; the hosting move (another epic).

## Success criteria

Each item must be something a person can check without technical help.
- [ ] Verify on the reviews page opens a finished report with screenshots and a clean console status.
- [ ] A change to the reviews page produces a matching before and after pair.
- [ ] A deliberately planted fake email stops the run and nothing is shared.
- [ ] Verify prints a private link for a clean report and prints no link when a masking check fails.
- [ ] A pull request draft for a real change is complete and waits for the owner's approval.

## Child issues

In the order they should be done. One child is one pull request.
- [x] Browser check in verify: start the app, drive the page, screenshots, console and network status (done, see #8)
- [x] Verify report as a local file: template, builder script, opens by itself (done, see #8)
- [x] Share the report: private link, privacy and approval rule, when something becomes an artifact (done, see #8)
- [x] Before and after screenshots on the same demo data (done, see #8)
- [x] Mask sensitive data in screenshots and logs, with an automatic scan that stops the run (done, see #8)
- [x] Pull request draft with evidence: evidence link, local image folder, one worked example (done, see #8)

## Dependencies and risks

| Item | Dependency or risk | Effect if it goes wrong | What we do about it | Owner |
|---|---|---|---|---|
| The Chrome extension must work on this machine | dependency | No screenshots | Test it in the first child; stop and ask after three failed clicks | Hung Le |
| Demo data must be the same on every run | risk | Before and after cannot be compared | Not checked yet; check in the before and after child | Hung Le |
| Screenshots may show personal data | risk | Personal data leaves the machine | Mask first, scan, and publish nothing if a check fails | Hung Le |
| GitHub cannot show private images | dependency | Images do not appear in the pull request | The pull request holds the link; images are dragged in by hand | Hung Le |

## Open questions

| Question | Proposal | Owner | Decided on |
|---|---|---|---|
| Which fields are sensitive? | Customer names, review text and emails | Hung Le | open |

## Scope changes

Every change of scope is written here with its reason, never made silently.

| Date | Change | Reason |
|---|---|---|
| 2026-10-16 | This epic was created by splitting the first single epic (31 tasks) into three | An epic should have 3 to 10 children |

## Environment

dev

## Attachments

Source: the team deck "Working with Claude Code" (October 2026) and the team chat. To be added: evidence when the children are done.
