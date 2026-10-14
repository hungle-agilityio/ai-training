---
name: write-ticket
description: Write or update a ticket (bug, feature or task) as a folder in docs/bugs/ with 4 files (reported, analysis, discussion, final). Use when the user gives a bug report, a feature request ("can we add X") or a piece of work, when the reporter has answered our questions, or when asked to analyse, reproduce, clarify or fill in a BUG, FEAT or TASK ticket.
---

# Write a ticket

The ticket is read by QA, BA, clients and devs, so anyone must understand it and follow it without asking questions.

## 1. Folder and stages

Every ticket is a folder `docs/bugs/<ID>/` (for example `docs/bugs/BUG-001/`) with four files, one per stage:

| File | Stage | Template | Contains |
|---|---|---|---|
| `01-reported.md` | The ticket as reported, not enough information yet | `docs/templates/01-reported.md` | Reporter, date, description **verbatim**, attachments the reporter sent. Never edited afterwards. |
| `02-analysis.md` | Our review | `docs/templates/02-analysis.md` | Type, labels, where, Analysis (3 sentences), what we found so far, numbered Questions for the reporter |
| `03-discussion.md` | The conversation between the reporter and the assignee | `docs/templates/03-discussion.md` | Every message in order (date, who), answers to our questions, new information and decisions, an "Answers so far" table and a readiness checklist. This is where questions are answered and information is added. |
| `04-final.md` | The complete issue, built from the discussion. It is posted as a standalone GitHub issue | `docs/templates/04-final-<bug\|feature\|task>.md` | Reporter, date, type, labels, Summary, then reproduction steps (bug), acceptance criteria (feature) or scope and done-when (task) |

Workflow:
1. **New report** → create the folder and `01-reported.md`.
2. **Review** → create `02-analysis.md` (do the work in section 3 first), `03-discussion.md` (no messages yet, answers table listing the questions as "Waiting"), then a draft `04-final.md` with everything already known.
3. **Discussion** → when the user passes on a message from the reporter, or says the questions were sent, record it in `03-discussion.md` (date, who wrote it, their words) and update the "Answers so far" table. Never write a reply the reporter did not give, and never say a question was sent unless the user says so. New questions go into the conversation and into `02-analysis.md` as new numbered questions.
4. **Final** → only when the discussion has enough information (checklist at the bottom of `03-discussion.md`), fold each answer into the sections of `04-final.md` it changes (Summary, steps, Expected, Actual, Environment, acceptance criteria, scope, labels such as `env`), remove `(proposal)` marks that were confirmed, and remove the `needs-info` label once nothing is left to ask. Do not add a section that lists answers or open questions, and do not change `01`.

## 2. Pick the type

| Type | Use when | Final template | ID / folder | Branch |
|---|---|---|---|---|
| `BUG` | Something that worked, or should work, is wrong: error, wrong value, slow, wrong text | `04-final-bug.md` | `BUG-<number>` | `bug/<id>-...` |
| `FEAT` | Users get a new ability, or an existing page changes what users see | `04-final-feature.md` | `FEAT-<number>` | `feat/<id>-...` |
| `TASK` | Work with no new user-facing behaviour: cleanup, data update, configuration, document, investigation | `04-final-task.md` | `TASK-<number>` | `task/<id>-...` |

- If the type is unclear, decide from the table and say which you chose and why. If the user names a type, use it.
- Use the next free number for that type, or the existing folder if the ticket already exists.
- Title format `[type] title`, for example `[BUG] dashboard show wrong score number`. The ID goes in the separate `ID` field, not in the title.

## 3. Rules for every ticket

1. **Plain language only.** No code, file names, function names, stack traces, commits, branches, test names or technical terms (say "the page shows an error", not "ZeroDivisionError"; "one extra lookup per location", not "N+1"). Developers find the code themselves. Do not add a failing test or a technical section.
2. **Keep the original description verbatim** in `01-reported.md`.
3. **Never invent facts.** Anything unknown (which page, which value, which environment, who owns it, what "done" means) goes into "What is ambiguous" and Questions. Do not guess the environment: use the label `env: to confirm`. Never invent the reporter's answers; proposals are marked `(proposal)` until the reporter confirms.
4. **Where:** in `02-analysis.md` name the page and address, or the API or screen, and state plainly if it does not exist yet or is a completely new page. `04-final.md` has no Where line: the page or screen is named in the Summary and the steps.
5. **Steps = user actions only.** No install, migrate, seed or run-server commands. If specific data must exist, say it inside the numbered steps with the real names and numbers (open this address, Riverside has 3 reviews rated 4, 5 and 2, look at this). There is no separate "Data needed" section.
6. **Exact results.** Give the real values or texts ("shows 3, should show 3.67") and the calculation if there is one.
7. **Labels (same set everywhere):** type (`bug`, `feature`, `task`); area (`dashboard`, ...); for bugs the kind (`crash`, `wrong-data`, `performance`, `ui`, `wrong-output`, optionally `intermittent`) and the reproduction result (`reproduced`, `partly-reproduced`, `cannot-reproduce`); `high-priority` only if urgent; `needs-info` while the reporter has not answered all questions (remove it when the ticket is ready); `env: dev`, `env: staging`, `env: production` or `env: to confirm` (never guess; use `env: dev` for what you reproduced yourself locally, which is the dev environment); `deadline: <date>` only if one was given. Type line is just `Bug`, `New feature` or `Task`.
8. **Questions:** ask everything needed so nobody has to ask again, numbered, each with a proposal people can simply accept or change. For bugs always request a screenshot or screen recording, plus the exact error text for crashes.
9. **Attachments:** list what exists and what is still to be added, and by whom.
10. **Analysis in 3 sentences:** what it asks, what is ambiguous, first step.
11. **`04-final.md` stands alone.** It is posted as an independent GitHub issue, so it never refers to another file, to `01` or `02`, or to "above" or "below". Attachments list only the screenshot, recording, error text or example itself, or what is still to be added, never a file link. `02-analysis.md` may refer to `04-final.md` by name.

## 4. Rules per type

- **BUG:** Reproduce before you write. Run the app locally and follow your own steps. Before changing local data, back up `db.sqlite3` to the scratchpad and restore it afterwards. Record what you saw under "What we found so far", and fill Steps to reproduce, Expected result, Actual result and Environment in `04-final.md`. If you could not reproduce it, say so and use the label `cannot-reproduce`. Never open files named `*DO-NOT-OPEN*`.
- **FEAT:** Look at the app first (read it, run it) and describe what exists today as a person sees it. Turn every undefined rule (what "good" means, what a "week" is, time zone, one location or all, filters combined or not, what to show when there is nothing) into a question with a proposal. Write acceptance criteria as "When <situation>, the screen must <result>", including the empty case. Keep the `needs-info` label until the reporter confirms.
- **TASK:** Say exactly what is touched, or "nothing visible to users". If users see a change, it is a FEAT; if something is broken, it is a BUG. Every "Done when" item must be checkable by a non-technical person. State what is in and out of scope.

## 5. Git naming (only when asked to create a branch or commit)

Follow CLAUDE.md: branch as in the table above, commit message `title`, blank line, `detail`, blank line, `Part of <id>`.

## 6. Before you finish

Re-read as a person who has never seen the code: do they know where, what, and how to follow the steps and see the same result? Tell the user the stage reached, the status, what could not be reproduced or decided, and which questions are open.
