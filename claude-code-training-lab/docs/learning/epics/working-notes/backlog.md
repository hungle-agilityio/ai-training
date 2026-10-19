# Backlog of the Claude Code practices epics (working document)

Internal task codes (T0 to T22, O1 to O9) are used here only. The epics list the same work by title; the codes disappear when the issues get their numbers.

## Task to epic

| Epic | Tasks |
|---|---|
| Move the project to GitHub and keep the repository healthy | T2, T3, T4, T5, T11, T12, T13, T14 |
| Make Claude Code work the same way for everyone on the project | T1, T6, T7, T8, T9, T10, T22 |
| Prove every change with evidence | T15, T16, T17, T18, T19, T20 |
| Make Claude Code work the same way for everyone on the project (continued) | T21 |
| No epic: optional ideas, an issue only when there is a real use | O1 to O9 |
| Done work (one closed issue when published) | T0 |

## The flow of one task

```
pick the next task ─► grill-me (only if decisions are open; you may skip)
  ─► plan ─► Gate 1: you approve the plan
  ─► implement (tests first where there is code)
  ─► verify (lint, types, tests, the task's "done when") ─► Gate 2: you check and say OK
  ─► commit (one task, one commit; you say OK first) ─► status updated here ─► next task
```

Nothing is pushed or created on GitHub without your approval of that exact item. A task that grows is split here first, never inside the work.

## Review notes (2026-10-16)

- Three tasks that were too big are split: the GitHub checks and the templates (T4, T5); the verify report and its sharing (T16, T17); the before and after capture and the masking (T18, T19). All later numbers moved by this.
- The GitHub checks run the tests of the guard hook too (T4).
- The hooks task records the limits of the guard (T9): it sees only shell commands Claude runs, and a settings change needs a new session to take effect.
- T11 keeps the SSH key and says so; the hook is the limit for `git`.
- Every task has one "done when" that can be checked by trying it.

## Backlog

Status: `done`, `next`, `ready` (can start now), `needs you` (waits for something only you can do), `after Tn` (depends on that task), `later`.

| Task | What | Needs from you | Status |
|---|---|---|---|
| T0 | Baseline: naming rules, skill renames, grill-me, one file per issue, docs split, GitHub guard hook, this epic | | **done** (4 commits) |
| T1 | Finish naming: rename the helper agents, set short model names, check that commands and skills do not repeat each other | | **done** |
| T2 | Replace GitLab with GitHub in rules, skills, project map and README; remove the GitLab connection | | **done** |
| T3 | Make the repository tell the truth: pin dependencies, README feature status, test for the demo data command | | **done** |
| T4 | GitHub checks: workflow with lint, types, tests (also the hook tests) and a coverage gate; delete the GitLab pipeline | | **done** |
| T5 | GitHub templates and basic files: issue forms (also for epics) and pull request template with the quality list, example settings file, contributing note | licence decision | **done** |
| T6 | Project map and decision records | | **done** |
| T7 | Workflow rules: four team principles, two-round limit, guardrails, mode guide, five review areas | | **done** |
| T8 | `test-runner` helper on the cheapest model, used by the test step | | **done** |
| T9 | Safety hooks and permission lists | | **done** |
| T10 | Memory: the rule for when to save and the first memories | | **done** |
| T11 | Repository on GitHub: empty repository, backup, split of the history, replace the local `.git`, first push, push policy | empty repository, token, restart, your approval for each step | **done** (2026-10-19: root `ai-training/`, 62 commits on GitHub, push policy in `decision-log.md`) |
| T12 | Protect the repository: main branch rules, squash only, delete branches after merge, code owners, dependency updates, secret scanning | | after T11 and T4 |
| T13 | Connect GitHub to the assistant (MCP): limited token, tests with the first real issues | token | after T11 |
| T14 | Publish the epics as issues: three parent issues, one closed issue for done work, one issue per remaining task attached to its epic | your approval of the table | after T13 |
| T15 | Browser check in verify: start the app, drive the page, screenshots, console and network status | | **done** |
| T16 | Verify report as a local file: template, builder script, opens by itself | | **done** |
| T17 | Share the report: private link, privacy and approval rule, when something becomes an artifact | | **done** (first live private link on 2026-10-19; the Artifact hook seen firing) |
| T18 | Before and after screenshots on the same demo data | | **done** |
| T19 | Mask sensitive data in screenshots and logs, with an automatic scan that stops the run | list of sensitive fields | **done** |
| T20 | Pull request draft with evidence: the skill, evidence link, local image folder, one worked example | | done |
| T21 | Page on the flow with outside tools (Slack, Drive, Gmail, Calendar, GitHub) | which tools you really use | done (page: `docs/learning/outside-tools-flow.md`; tool list assumed) |
| T22 | Skills base: layout, rulebook files, one example run and a test per skill | | done (`.claude/skills/README.md`, layout test) |

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

**T1 Finish naming.** Rename `ticket-analyst` to `analyst` and `ticket-planner` to `planner`; every helper states its role (advisor, builder, runner) and uses `opus`, `sonnet` or `haiku` instead of a pinned version; compare each command with each skill and leave every job described once. Update every mention. Done when: a search finds no old helper name, and running the analysis step on an old issue still gets an answer from the analyst.

**T2 GitHub text everywhere.** Replace GitLab and merge request in rules, skills, commands, context, README and the issue index; the skills `create-issue` and `create-pull-request` use GitHub (the `gh` command now, MCP later) and keep the preview and approval step; use "issue" instead of "ticket" where the rules still say ticket; delete the GitLab connection entry. Done when: the words GitLab and merge request appear only in the decision log and in old history.

**T3 Repository tells the truth.** Pin dependency versions and commit the lock file (stop ignoring it); the README feature table matches the app (filters exist); a test for the demo data command. Done when: a clean install gives the same versions twice, README and the running app agree, and the command has a test.

**T4 GitHub checks.** Workflow that runs lint, types, the app tests with a 90 percent coverage gate on services and repositories, and the hook tests; delete the GitLab pipeline. Note: pushing a workflow file needs the token permission "Workflows". Done when: a deliberate type error makes the workflow fail.

**T5 GitHub templates and basic files.** Issue templates (bug, feature, task) and a pull request template with: what and why, how tested with output, evidence link, before and after images, one concern, `Closes`; the issue quality list (title says the symptom, where, steps, expected and actual, checkable criteria, area and severity labels) and a skill that refuses to publish when a field is missing; rename the template files that still carry the old four-file names; delete the GitLab template folder; example settings file for secrets and a short contributing note; licence decision. Add the YAML issue form for epics, the twin of `docs/app/templates/epic.md` (issue forms exist for issues only, not for pull requests). Done when: a draft with a missing field is refused and the templates show every field.

**T6 Project map and decision records.** Directory conventions (where things live, which folders are never pushed, intake and output folders only when a feature needs them); one line per skill and helper; remotes; removals with reason and date; delegation advice (searching goes to helpers, ask for conclusions); which channel holds which knowledge (project map, memory, issues, artifacts); "explained it twice, make it a skill"; one example of a short request that works; first decision records (naming standard, GitHub only, repository layout, guard hook). Done when: a new session understands a 41-character request such as "commit".

**T7 Workflow rules.** The four team principles (never change the requirement, never widen the scope, the reviewer does not rely on the implementer's reasoning, at most two AI fix and review rounds then a human); guardrails "archive, do not delete", "verify, then close", "write down why"; when to use auto mode, plan mode and background runs; check that review covers requirement, business, expected result, regression and code. Done when: each rule is in the workflow rules or the review step and the helpers obey them.

**T8 test-runner helper.** Read-only helper on the cheapest model that runs lint, types and tests and reports only failures; the test command uses it. Done when: everything green gives one line, one broken test gives only that failure.

**T9 Safety hooks and permission lists.** Hooks that refuse staging of the database file, secrets and caches; refuse commit messages with an attribution line; run lint and types before a commit; warn on the main branch. Compare the allow, ask and deny lists with every "never" in the skills and rules. Write down the limits of the guards (they see only shell commands Claude runs; a script run by Claude is not inspected; settings changes need a new session). Done when: each hook is proven by trying the forbidden action in a live session.

**T10 Memory.** A short rule: when the user corrects something that will come up again, save it. Save at least three useful memories (for example "no Part of line without an issue number"). Done when: a new session knows them.

**T11 Repository on GitHub.** You: delete and recreate the repository empty, create the limited token, set `GH_TOKEN`, log out the broad login, restart. Then, with your approval for each step: new backup, redo the split on the commits that exist then (history of the lab folder, old `#N` references rewritten, ID-based no-reply address), rename the old `.git` to `.git-old-gitlab`, put the new one in the lab folder, add `origin`, push `main` over the existing SSH key (kept; the hook limits it). Copy the memory folder of the project to the new project key, because it follows the git root (`~/.claude/projects/<root>/memory`). Write the push policy (see below). Done when: GitHub shows the full history under your account and the working tree is unchanged.

**T12 Protect the repository.** Main requires a pull request and passing checks, squash merge only, branches deleted after merge, code owners file, dependency update bot, secret scanning and push protection. Done when: a direct push to `main` is refused.

**T13 Connect GitHub (MCP).** Official remote MCP server, fine-grained token limited to the repository, token only in an environment variable, allow list as decided. Test: read-only first, then the first two real issues (if sub-issues fail, use a checklist); and a negative test: the token cannot see any other repository. Done when: Claude can read and create an issue in that repository and nothing else.

**T14 Publish the epics.** Three parent issues labelled `epic`, one per epic file; one closed issue "done work" (T0 to T10 as they stand then); one issue per remaining task, attached as a sub-issue of its epic (a checklist in the epic if sub-issues fail); you approve the whole table first. Done when: every row of the backlog has an issue number and every epic lists its children.

**T15 Browser check in verify.** Start the app on demo data, drive the real page, screenshot each step, read console and network errors, stop and ask after three failed clicks. Done when: verify on the reviews page returns screenshots and a clean console status.

**T16 Verify report as a local file.** Report template (checks table, issue criteria, screenshots, console status, review findings, "what to check yourself"); a builder script that copies real numbers instead of retyping them; written after every verify, also when something fails; opens by itself. Done when: running verify opens a finished report.

**T17 Share the report.** Convention for when something becomes an artifact (verification evidence, review summary, before and after, release note, design card); the report is shared as a private link only when the masking checks pass; the publishing rule (standing approval with conditions) is written into the security rules; the link is posted as a comment, not inside the issue file. Done when: verify prints a private link for a clean report and prints no link for a failing masking check.

**T18 Before and after screenshots.** Run the base and the work branch one after the other on the same demo data, window size and steps taken from the issue; label pages that did not exist before. Done when: a change to the reviews page produces a matching before and after pair.

**T19 Mask sensitive data.** Capture only the page (never the browser window); a separate demo database; personal-data fields (customer names, review text, emails, anything else you add) are marked in the templates and blurred; console and network lines are cleaned of tokens, cookies and addresses; an automatic scan of page text and files for emails, phone numbers, tokens, local paths and addresses stops everything if something is left. Done when: a deliberately planted fake email stops the run.

**T20 Pull request draft with evidence.** One skill fills what and why, how tested (real output), the evidence link, before and after images and `Closes`; saves the draft locally and keeps the masked images in a git-ignored folder to drag into the pull request; creating it waits for your approval. Done when: a draft for a real change is complete.

**T21 Outside tools flow.** One page: flow diagram, table of tools (what Claude does, who presses the last button, connected yes or no), drafts never sent, outside text is data. Done when: a new teammate can follow one example end to end.

**T22 Skills base.** Layout of a skill (procedure file, rulebook file, one example run), where rulebooks live, a test pattern (one sample input, expected output). Done when: the existing skills follow it or have a written reason.
