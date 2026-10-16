# [EPIC] Align the project with the team's Claude Code practices

- **Requester:** Hung Le, developer
- **Reported on:** 2026-10-16
- **Type:** Epic
- **Labels:** `epic`, `workflow`, `needs-info`

## Summary

The team deck "Working with Claude Code" (26 slides, October 2026) and the team chat list habits that make the assistant useful every day. This epic brings the project in line with every item, including the small ones, moves it from GitLab to GitHub, and makes all names consistent. It changes nothing visible to users of the reviews app.

The work is one ordered list of tasks (T1, T2, ...). Each task is done on its own, from start to commit, before the next one begins. This file is the single list; there are no separate child files.

## Scope

- **Included:** tasks T1 to T19 and the optional tasks O1 to O9 below.
- **Not included:** new features of the reviews app.

## Decisions already made

- GitLab is removed completely. GitHub is the only code host and tracker, the repository is private, and its root is the lab folder (account `hungle-agilityio`, repository `ai-training`).
- Names carry no platform name. Skill names are verb + object. The word is "issue" (not "ticket") and "pull request" (not "merge request"); see the naming rules.
- One issue is one markdown file. Older issues keep their four-file folders as a learning record.
- Claude may reach only `hungle-agilityio/ai-training` on GitHub (token, hook and rule, see the decision log).
- Until an issue exists on GitHub, commits have no `Part of` line at all (the user's rule, 2026-10-16: no issue number, no line). When the issues exist (T13), commits use `Part of #<number>`.

## The flow of one task

```
pick the next task ─► grill-me (only if decisions are open; you may skip)
  ─► plan ─► Gate 1: you approve the plan
  ─► implement (tests first where there is code)
  ─► verify (lint, types, tests, the task's "done when") ─► Gate 2: you check and say OK
  ─► commit (one task, one commit; you say OK first) ─► status updated here ─► next task
```

Nothing is pushed or created on GitHub without your approval of that exact item. A task that grows is split here first, never inside the work.

## Backlog

Status: `done`, `next`, `ready` (can start when the earlier ones are done), `needs you` (waits for something only you can do), `after Tn` (depends on that task), `later`.

| Task | What | Needs from you | Status |
|---|---|---|---|
| T0 | Baseline: naming rules, skill renames, grill-me, one file per issue, docs split, GitHub guard hook | | **done** (4 commits) |
| T1 | Finish naming: rename the helper agents and set short model names; check that commands and skills do not repeat each other | | **next** |
| T2 | Replace GitLab with GitHub in rules, skills, project map and README; remove the GitLab connection | | ready |
| T3 | Make the repository tell the truth: pin dependencies, README feature status, test for the demo data command | | ready |
| T4 | GitHub checks and templates: workflow (lint, types, tests, coverage gate), issue and pull request templates with the quality list, basic files | licence decision | ready, after T2 and T3 |
| T5 | Project map and decision records: directory conventions, one line per skill and helper, removals with reason and date, first records | | ready |
| T6 | Workflow rules: four team principles, two-round limit, guardrails, mode guide, five review areas | | ready |
| T7 | `test-runner` helper on the cheapest model, used by the test step | | ready |
| T8 | Safety hooks and permission lists: remaining hooks, compare the lists with every rule in the skills | | ready |
| T9 | Memory: the rule for when to save and the first memories | | ready |
| T10 | Repository on GitHub: empty repository, backup, split of the history, replace the local `.git`, first push, push policy | empty repository, token, restart, your approval for each step | **needs you** |
| T11 | Protect the repository: main branch rules, squash only, delete branches after merge, code owners, dependency updates, secret scanning | | after T10 and T4 |
| T12 | Connect GitHub to the assistant (MCP): limited token, tests with the first real issues | token | after T10 |
| T13 | Publish the epic as issues: parent issue, one closed issue for done work, one issue per remaining task, linked | your approval of the table | after T12 |
| T14 | Browser check in verify: start the app, drive the page, screenshots, console and network status | | ready |
| T15 | Verify report: template, builder script, opens by itself, shared as a private link, privacy and approval rule | | after T14 |
| T16 | Before and after screenshots with masking of sensitive data | list of sensitive fields | after T14 |
| T17 | Pull request draft with evidence: the skill, evidence link, local image folder, one worked example | | after T4, T15, T16 |
| T18 | Page on the flow with outside tools (Slack, Drive, Gmail, Calendar, GitHub) | which tools you really use | ready |
| T19 | Skills base: layout, rulebook files, one example run and a test per skill | | ready |

Optional, only if needed (each can be dropped with a written reason):

| Task | What | Old items |
|---|---|---|
| O1 | Connect and test Slack, Drive, Gmail, Calendar | P29 |
| O2 | Skill `intake-document` | P42.2 |
| O3 | Skills `generate-docx` and `generate-pptx` | P42.3, P42.4 |
| O4 | Skill `plan-sprints`, plan-to-tracker sync and AI work queue | P42.5, P31 |
| O5 | Skill `generate-timesheet` | P42.6 |
| O6 | Skill `sync-repositories` (pushes still wait for your approval) | P42.7 |
| O7 | One working folder per issue | P30 |
| O8 | Remote access kit (session wrapper, remote control, tunnels) | P32 |
| O9 | HTML design cards for screens | P33 |

Dropped: P24, clean merged local branches. The new repository starts with `main` only and the old branches stay in the backup.

## Task cards

**T1 Finish naming.** Rename `ticket-analyst` to `analyst` and `ticket-planner` to `planner`; every helper states its role (advisor, builder, runner) and uses `opus`, `sonnet` or `haiku` instead of a pinned version; compare each command with each skill and leave every job described once. Update every mention. Done when: a search finds no old helper name; the analyst and planner still answer.

**T2 GitHub text everywhere.** Replace GitLab and merge request in rules, skills, commands, context, README and the issue index; skills `create-issue` and `create-pull-request` use GitHub (`gh` and later MCP) and keep the preview and approval step; delete the GitLab connection entry. Done when: the words GitLab and merge request appear only in the decision log and in old history.

**T3 Repository tells the truth.** Pin dependency versions and commit the lock file (stop ignoring it); README feature table matches the app (filters exist); a test for the demo data command. Done when: a clean install gives the same versions twice; README and the running app agree; the command has a test.

**T4 GitHub checks and templates.** Workflow with lint, types, tests and a 90 percent coverage gate; issue templates (bug, feature, task) and a pull request template with: what and why, how tested with output, evidence link, before and after images, one concern, `Closes`; issue quality list (title says the symptom, where, steps, expected and actual, checkable criteria, area and severity labels); example settings file for secrets, a short contributing note; licence decision; delete the GitLab pipeline and templates; rename the template files that still carry the old four-file names. Done when: a type error fails the workflow; the templates show every field. Note: the workflow file needs the token permission "Workflows" to be pushed.

**T5 Project map and decision records.** Directory conventions (where things live, which folders are never pushed, intake and output folders only when a feature needs them); one line per skill and helper; remotes; removals with reason and date; delegation advice (searching goes to helpers, ask for conclusions); which channel holds which knowledge (project map, memory, issues, artifacts); one example of a short request that works; "explained it twice, make it a skill"; first decision records (naming standard, GitHub only, repository layout). Done when: a new session understands a 41-character request such as "commit".

**T6 Workflow rules.** Four team principles (never change the requirement, never widen the scope, the reviewer does not rely on the implementer's reasoning, at most two AI fix and review rounds then a human); guardrails "archive, do not delete", "verify, then close", "write down why"; when to use auto mode, plan mode and background runs; check that review covers requirement, business, expected result, regression and code. Done when: each rule is in the workflow rules or the review step and the helpers obey them.

**T7 test-runner helper.** Read-only helper on the cheapest model that runs lint, types and tests and reports only failures; the test command uses it. Done when: everything green gives one line, one broken test gives only that failure.

**T8 Safety hooks and permission lists.** Add hooks: refuse staging of the database file, secrets and caches; refuse commit messages with an attribution line; run lint and types before a commit; warn on the main branch. Compare the allow, ask and deny lists with every "never" in the skills and rules. Done when: each hook is tested by trying the forbidden action.

**T9 Memory.** A short rule: when the user corrects something that will come up again, save it. Save at least three useful memories (for example "no attribution line in commits"). Done when: a new session knows them.

**T10 Repository on GitHub.** You: delete and recreate the repository empty, create the limited token, set `GH_TOKEN`, log out the broad login, restart. Then, with your approval for each step: new backup, redo the split on the commits that exist then (history of the lab folder, old `#N` references rewritten, ID-based no-reply address), rename the old `.git` to `.git-old-gitlab`, put the new one in the lab folder, add `origin`, push `main`. Write the push policy (see below). Done when: GitHub shows the full history under your account and the working tree is unchanged.

**T11 Protect the repository.** Main requires a pull request and passing checks, squash merge only, branches deleted after merge, code owners file, dependency update bot, secret scanning and push protection. Done when: a direct push to `main` is refused.

**T12 Connect GitHub (MCP).** Official remote MCP server, fine-grained token limited to the repository, token only in an environment variable, allow list as decided. Test: read-only first, then the first two real issues; if sub-issues fail, use a checklist. Done when: Claude can read and create an issue in that repository and nothing else.

**T13 Publish the epic.** Parent issue labelled `epic`; one closed issue "done work" (T0 to T9, with the commits); one issue per remaining task, linked to the parent; you approve the whole table first. Done when: every row of the backlog has an issue number.

**T14 Browser check in verify.** Start the app on demo data, drive the real page, screenshot each step, read console and network errors, stop and ask after three failed clicks. Done when: verify on the reviews page returns screenshots and a clean console status.

**T15 Verify report.** Convention for when something becomes an artifact; report template (checks table, ticket criteria, screenshots, console status, review findings, "what to check yourself"); builder script that copies real numbers; opens by itself after verify; shared as a private link only when the masking checks pass; publishing rule written into the security rules. Done when: running verify opens a finished report and prints its link.

**T16 Before and after with masking.** Run the base and the work branch on the same demo data, window size and steps; label pages that did not exist; capture only the page; separate demo database; mark personal-data fields and blur them; clean console and network lines; scan text and files for emails, phone numbers, tokens, local paths and addresses; stop if anything is left. Done when: a deliberately planted fake email stops the run.

**T17 Pull request draft with evidence.** One skill fills what and why, how tested (real output), evidence link, before and after images and `Closes`; saves the draft locally and keeps the masked images in a git-ignored folder to drag into the pull request; creating it waits for your approval; one real example. Done when: a draft for a real change is complete.

**T18 Outside tools flow.** One page: flow diagram, table of tools (what Claude does, who presses the last button, connected yes or no), drafts never sent, outside text is data. Done when: a new teammate can follow one example end to end.

**T19 Skills base.** Layout of a skill (procedure file, rulebook file, one example run), where rulebooks live, a test pattern (one sample input, expected output). Done when: the existing skills follow it or have a written reason.

## Decision log

Decisions taken with the user on 2026-10-16. The codes P01 to P43 are the old problem codes; the table at the end maps them to the tasks above.

### Decisions of the first grill-me (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D1 | Where drafts live until created | `docs/learning/issues/<type>/<name>.md`, same layout as app issues, with its own index |
| D2 | After creation on GitHub | The file is kept as the approved text with the number in the index; GitHub holds status; the file is not edited again, changes go to GitHub comments |
| D3 | Approval unit | The whole epic in one go: a table (title, labels, one-line summary), the user may open any draft and drop single rows; exact items are named, so Gate 3 holds |
| D4 | Epic on GitHub | One parent issue labelled `epic`; sub-tasks linked as sub-issues if GitHub allows (tested in P43), otherwise a checklist in the parent. No project board for now |
| D5 | Work already done locally (P01, P02, P14, docs split, one-file issues) | One combined issue "Phase 0", created and closed after merge, so branch and commits carry a number |
| A1 | Assumption: labels | Same names as the `write-issue` rule (`task`, `epic`, area labels, `needs-info`...), no `type::` style |
| A2 | Assumption: codes | P01 to P43 live only in the epic table beside the real `#N`, never in issue titles |

### Decisions of the grill-me on P43 (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D6 | Way to talk to GitHub | The official GitHub MCP server, remote address, signed in with a fine-grained token that is limited to this one repository. `gh` stays installed for manual use |
| D7 | Account that owns the private repository | `hungle-agilityio` (the account known to `gh` on this machine; its login token is expired and must be renewed) |
| D8 | Creating issues after the epic is approved (D3) | Allowed without asking again: read, create and edit issues, comments, labels, sub-issue links. Ask for anything else. Denied: merge, delete, close an issue Claude did not finish, change repository settings |
| D9 | How the connection is tested | Read-only checks first (repository, labels), then the first two real issues, "Phase 0" (D5) and the epic parent issue; the link between them tests sub-issues. If sub-issues fail, use a checklist in the parent |
| A3 | Assumption: token | An environment variable; `.mcp.json` only names the variable; Claude never reads or prints it and never writes it to a file |
| A4 | Assumption: shared file | `.mcp.json` is committed (no secret in it) and the GitLab entry is removed |
| A5 | Assumption: pushing code | Still goes through SSH keys and still asks each time; it does not use this token |
| A6 | Assumption: sign-in | The user types `! gh auth login -h github.com` in this session when asked |

### Decisions of the grill-me on P34 and P05 (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D10 | History | Keep the whole history of the lab folder (37 commits, folder prefix removed) and rewrite the old GitLab references `#1`, `#2`, `#4` in commit messages to `GitLab #1`, `GitLab #2`, `GitLab #4`, so they do not link to the wrong GitHub issues |
| D11 | Author in old commits | Rewrite to the GitHub no-reply address of `hungle-agilityio` (exact address taken from the GitHub email settings), and set the same address for new commits in this repository |
| D12 | Repository name | `ai-training` |
| D13 | Old repository | Mirror backup outside the folder, stash exported with it, then rename the old `.git` to `.git-old-gitlab` (reversible); the lab folder gets its own new `.git`; the parent folder keeps its README and `.claude` but is no longer a repository |
| D14 | The 86 uncommitted changes | The split uses only committed history and becomes `main`; afterwards the "Phase 0" issue (D5) exists, a branch `task/<number>-...` is made in the new repository, all current changes are committed with `Part of #<number>` and go through a pull request. A copy of the working tree is made first |
| A7 | Assumption: branches | Only `main` is published (it holds the full history); the merged bug and feature branches are not pushed |
| A8 | Assumption: first push | The first push of `main` is an import and the single exception to "never commit directly to main" |
| A9 | Assumption: remotes | The new remote is `origin` to GitHub; no GitLab remote in the new repository; the old GitLab project is not touched |
| A10 | Assumption: old worktree | `source-tree-display-40a149` is left alone until the user says so |
| A11 | Assumption: every git step | A concrete plan is shown and approved before each hard-to-undo step (split, rename of `.git`, create repository, push) |

Note on D12: the repository is named `ai-training` while the content is the lab, so a second project cannot share this root; also the local parent folder keeps the same name but stops being a repository.

### Decisions of the grill-me on limiting GitHub access (2026-10-16)

| ID | Decision | Answer |
|---|---|---|
| D15 | Credentials (amended 2026-10-16) | One fine-grained token limited to `hungle-agilityio/ai-training` for `gh` and the MCP server; the broad `gh` login is logged out afterwards. `git push` and `git pull` stay on the existing SSH key, which the user keeps; because GitHub does not limit that key to one repository, the hook is what stops Claude from pushing, pulling, reading or writing any other repository |
| D16 | Existing repository with an automatic first commit | The user deletes it and creates it again empty (no README, no licence); the token is created after that, because it is tied to the repository |
| D17 | Guard inside Claude Code | A hook that blocks `gh`, `git` and `curl` commands reaching another repository, plus allow, ask and deny lists and a default `GH_REPO`; written and tested 2026-10-16 |
| D18 | Where each rule lives | Token = hard boundary; hook and lists = enforcement; `rules/security.md` and decision records = explanation; the token itself only in an environment variable |
| A12 | Decision by the user: SSH key | The key is NOT removed and stays in use for `git`; only access to other repositories is blocked (by the hook for Claude's commands) |
| A13 | Assumption: limits | The guard stops only commands Claude itself runs through the shell tool. It cannot see what a script run by Claude does inside (for example a Python file calling `gh`), nor commands the user types; those are limited only by the token (API) and not at all for `git` over SSH |
| A14 | Assumption: split email | The ID-based no-reply address `104913131+hungle-agilityio@users.noreply.github.com` replaces the earlier username-only form (step 2 redone and verified) |

Token permissions for the user to set: owner `hungle-agilityio`, only repository `ai-training`; Metadata read; Contents read and write; Issues read and write; Pull requests read and write; no Administration, no Actions; Workflows only when CI is added (P06); expiry 30 to 90 days.

Order inside Phase 1 because of D6: P34 (repository from the lab folder), P05 (remote), then P43 (create the token for that one repository, set the variable, connect, test). The GitHub user name for assignee is `hungle-agilityio` (D7).

## Push policy (proposal, confirmed in task T10)

| Push | Never push | Your decision |
|---|---|---|
| App code, tests, dependency list and lock file | Database file, `.env` files, tokens, keys | The trainer answer-key file in the issues folder |
| Team assistant settings: project map, rules, context, knowledge, commands, skills, agents, shared `settings.json` | Personal assistant settings and personal notes (`settings.local.json`, `CLAUDE.local.md`), memory, session logs | The learning journal |
| GitHub workflow, templates, code owners | Virtual environment, caches, coverage output, `.DS_Store` | The copied course notes (check the licence before making the repo public) |
| Issues folder, epic, decision records, README | Working copies and scratch files, real customer data | Repository visibility (private recommended for now) |

Process: nothing is pushed without approval of that exact item; one branch per issue and a pull request into main; run verify first; look at the list of staged files before every commit; never force.

## Where each slide item goes

| Slide | Item | Task(s) |
|---|---|---|
| 2 | Numbers baseline (information only) | none |
| 3, 6 | Explained twice means make it a skill; rules in a rulebook file; the five example skills (intake, docx/pptx, sprint plan, timesheet, repo sync) | T1, T5, T19 |
| 4 | Talk like a teammate (short working-style note) | T5 |
| 5 | Project map: where things live, one line per skill, repos and remotes, removals with reason and date, update with the change | T5, T2 |
| 7 | Connectors; drafts not sends; browser for tools without a connector | T18, O1 |
| 8 | grill-me before planning | T0 |
| 9 | One plan, synced both ways with the tracker | O4 |
| 10 | HTML design until clear | O9 |
| 11 | Opus advisor, Sonnet builder, Haiku runner; models set in each helper | T1, T7 |
| 12 | Auto mode, plan mode, background runs | T6 |
| 13 | One workstream, one checkout; resume; new topic means new workstream | O7, O8 |
| 14 | Delegate searching, ask for conclusions | T5, T7 |
| 15 | Issues as AI work queue, release never close | O4 |
| 16 | Issues and pull requests a stranger can act on | T4 |
| 17 | Channels for sharing knowledge | T5, T9 |
| 18, 19, 20 | Remote reach, session wrapper, naming, pinned session id, tunnels | O8 |
| 21, 22 | Artifacts, diagrams, screenshots, animation | T15 |
| 23 | End-to-end check in a real browser | T14, T3 |
| 24 | Guardrails: no force push, honest commits, archive not delete, verify then close, write down why | T8, T6, T5 |
| 25 | Memory, hooks, pipeline tests, prune workspaces | T9, T8, T4, T3 (prune: dropped, see Backlog) |
| 26 | Five first steps | T5, T0, T1, O7, T14 |
| Team chat | Four principles; two-round limit; five review areas | T6 |

## Old problem codes to tasks

| Old code | Task |
|---|---|
| P01 | T0 |
| P02 | T0 |
| P03 | T1 |
| P04 | T1 |
| P05 | T10 |
| P06 | T4 |
| P07 | T4 |
| P08 | T2 |
| P09 | T2 |
| P10 | T5 |
| P11 | T3 |
| P12 | T3 |
| P13 | T5 |
| P14 | T0 |
| P15 | T6 |
| P16 | T6 |
| P17 | T7 |
| P18 | T6 |
| P19 | T19 |
| P20 | T8 |
| P21 | T8 |
| P22 | T9 |
| P23 | T3 |
| P24 | dropped (the new repository starts with main only; old local branches stay in the backup) |
| P25 | T14 |
| P26 | T15 |
| P26.1 | T15 |
| P26.2 | T15 |
| P26.3 | T15 |
| P26.4 | T14 |
| P26.5 | T15 |
| P26.6 | T17 |
| P26.7 | T15 |
| P26.8 | T17 |
| P26.9 | T15 |
| P26.10 | T15 |
| P26.11 | T16 |
| P26.12 | T16 |
| P26.13 | T17 |
| P27 | T4 |
| P28 | T18 |
| P29 | O1 |
| P30 | O7 |
| P31 | O4 |
| P32 | O8 |
| P33 | O9 |
| P34 | T10 |
| P35 | T11 |
| P36 | T11 |
| P37 | T4 |
| P38 | T10 |
| P39 | T10 |
| P40 | T5, T6 |
| P42 | T19 |
| P42.1 | T19 |
| P42.2 | O2 |
| P42.3 | O3 |
| P42.4 | O3 |
| P42.5 | O4 |
| P42.6 | O5 |
| P42.7 | O6 |
| P42.8 | T19 |
| P43 | T12 |

## Done when

- [ ] Every task T1 to T19 is `done`, or dropped with a written reason; every optional task is done or dropped with a reason.
- [ ] Every row of the slide table points to a done task.
- [ ] The words GitLab and merge request appear only in the decision log.
- [ ] Old skill and helper names appear nowhere.
- [ ] A branch can be pushed to GitHub, always after approval, and the guard hook blocks every other repository.

## Steps to check the result

1. Open the project map and follow each link.
2. Ask the assistant to commit with an attribution line: it is refused.
3. Search the project for the old names and for GitLab: nothing is found.

## Expected result

The project follows the deck, uses one naming pattern, lives on GitHub and enforces its safety rules automatically.

## Environment

dev

## Attachments

Source: the team deck and the team chat screenshot. To be added: the naming table and the flow diagram.
