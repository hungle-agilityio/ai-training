# Epics: Claude Code practices

The team deck "Working with Claude Code" (26 slides, October 2026) and the team chat list habits that make the assistant useful every day. This epic brings the project in line with every item, including the small ones, moves it from GitLab to GitHub, and makes all names consistent. It changes nothing visible to users of the reviews app.

The work is split into three epics, each with 3 to 10 children, built from the epic template (`docs/app/templates/epic.md`). Each child is done on its own, from start to commit, before the next one begins.

## Epics

| Epic | Children |
|---|---|
| [Move the project to GitHub and keep the repository healthy](github-and-repository-health.md) | 8 |
| [Make Claude Code work the same way for everyone on the project](team-conventions-and-workflow.md) | 8 |
| [Prove every change with evidence: browser check, reports and pull request drafts](evidence-and-reports.md) | 6 |

Optional ideas from the deck (connect Slack, Drive, Gmail and Calendar, `intake-document`, `generate-docx` and `generate-pptx`, `plan-sprints` with an AI work queue, `generate-timesheet`, `sync-repositories`, one working folder per issue, remote access kit, HTML design cards) are not an epic: they stay in the working notes and get an issue only when there is a real use.

Work already done (naming rules, skill renames, grill-me, one file per issue, docs split, guard hook, these epics) becomes one closed issue when the epics are published.

## Working documents

- [`working-notes/backlog.md`](working-notes/backlog.md): status of every task, the flow of one task, the task cards.
- [`working-notes/decision-log.md`](working-notes/decision-log.md): decisions, push policy.
- [`working-notes/slides-coverage.md`](working-notes/slides-coverage.md): which task covers each slide item, old codes.

## Rules for an epic

- One outcome, written as a goal in one sentence, with success criteria that anyone can check.
- Between 3 and 10 children, in order; one child is one pull request; more than that means the epic is split.
- Children are sub-issues of the epic (a checklist if sub-issues are not available).
- Every change of scope is written in the epic with its reason.
- An epic file stands alone: it does not refer to other files.

## Decisions already made

- GitLab is removed completely. GitHub is the only code host and tracker, the repository is private, and its root is the lab folder (account `hungle-agilityio`, repository `ai-training`).
- Names carry no platform name. Skill names are verb + object. The word is "issue" (not "ticket") and "pull request" (not "merge request"); see the naming rules.
- One issue is one markdown file. Older issues keep their four-file folders as a learning record.
- Claude may reach only `hungle-agilityio/ai-training` on GitHub (token, hook and rule, see the decision log).
- Until an issue exists on GitHub, commits have no `Part of` line at all (the user's rule, 2026-10-16: no issue number, no line). When the issues exist (T13), commits use `Part of #<number>`.
