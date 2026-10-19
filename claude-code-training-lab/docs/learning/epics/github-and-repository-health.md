# [EPIC] Move the project to GitHub and keep the repository healthy

- **Owner:** Hung Le, developer
- **Reported on:** 2026-10-16
- **Type:** Epic
- **Labels:** `epic`, `hosting`, `needs-info`
- **Milestone:** none yet

## Goal

The project lives in a private GitHub repository under the account `hungle-agilityio`, with automatic checks, a protected main branch and templates, and nothing in the project mentions GitLab.

## Why

GitLab is being dropped. The rules and skills still describe GitLab, the automatic checks do not match the project rules (no type check, no coverage gate), dependency versions are not pinned, and the README is out of date.

## Scope

- **Included:** GitHub wording everywhere; pinned dependencies and a true README; automatic checks; templates; moving the history; protection of the main branch; connecting the assistant; creating the issues of all epics.
- **Not included:** New features of the reviews app; moving old GitLab issues; the work of the other epics.

## Success criteria

Each item must be something a person can check without technical help.
- [ ] The words GitLab and merge request appear nowhere in the project except in one decision record.
- [ ] A clean install gives the same dependency versions twice.
- [ ] A deliberate type error makes the automatic checks fail on GitHub.
- [ ] GitHub shows the full history of the lab folder under the account `hungle-agilityio`, and a direct push to `main` is refused.
- [ ] The assistant can read and create an issue in this repository and cannot reach any other repository.

## Child issues

In the order they should be done. One child is one pull request.
- [x] Replace GitLab with GitHub in rules, skills and README (done, see #8)
- [x] Make the repository tell the truth: pin dependencies, README status, test for the demo data command (done, see #8)
- [x] GitHub checks: lint, types, tests (also the hook tests) and a coverage gate (done, see #8)
- [x] GitHub templates and basic files: issue forms (also for epics), pull request template, example settings file, contributing note (done, see #8)
- [x] Repository on GitHub: backup, history split, first push (done, see #8)
- [ ] Protect the repository: main branch rules, code owners, dependency updates, secret scanning (#9)
- [ ] Connect GitHub to the assistant: limited token and tests (#5)
- [ ] Publish the epics as issues (#7)

## Dependencies and risks

| Item | Dependency or risk | Effect if it goes wrong | What we do about it | Owner |
|---|---|---|---|---|
| GitHub account, empty repository and limited token | dependency | Nothing can be pushed or created | The owner creates them; the steps are written in the repository task | Hung Le |
| Splitting the history changes the commit ids | risk | Old ids in notes stop matching | A backup is kept and the split is checked by comparing the content | Hung Le |
| The token expires (30 to 90 days) | risk | The assistant loses access | A reminder is set when the token is made | Hung Le |
| Pushing a workflow file needs the Workflows permission on the token | dependency | The checks cannot be pushed | Add the permission when the checks task starts | Hung Le |
| The guard only sees shell commands that Claude runs | risk | Another repository could be reached some other way | The token limits the API; commands typed by the owner are out of its reach | Hung Le |

## Open questions

| Question | Proposal | Owner | Decided on |
|---|---|---|---|
| Which licence, if any? | None for now: the repository is private | Hung Le | open |

## Scope changes

Every change of scope is written here with its reason, never made silently.

| Date | Change | Reason |
|---|---|---|
| 2026-10-16 | This epic was created by splitting the first single epic (31 tasks) into three | An epic should have 3 to 10 children |

## Environment

dev

## Attachments

Source: the team deck "Working with Claude Code" (October 2026) and the team chat. To be added: evidence when the children are done.
