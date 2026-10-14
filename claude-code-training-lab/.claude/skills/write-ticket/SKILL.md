---
name: write-ticket
description: Write one complete, standalone ticket (bug, feature or task) from a description, following the project templates, and save it as docs/bugs/<ID>/04-final.md. Use when the user gives a bug report, a feature request ("can we add X") or a piece of work, when new information arrives for an existing ticket, or when asked to analyse, reproduce, clarify or fill in a BUG, FEAT or TASK ticket.
---

# Write a ticket

The ticket is read by QA, BA, clients and devs, so anyone must understand it and follow it without asking questions. It is posted as a standalone GitHub issue.

## 1. Output: one file

Write **one** file: `docs/bugs/<ID>/04-final.md`, the complete ticket, built from the template of its type:

| Type | Use when | Template | ID / folder | Branch |
|---|---|---|---|---|
| `BUG` | Something that worked, or should work, is wrong: error, wrong value, slow, wrong text | `docs/templates/04-final-bug.md` | `BUG-<number>` | `bug/<id>-...` |
| `FEAT` | Users get a new ability, or an existing page changes what users see | `docs/templates/04-final-feature.md` | `FEAT-<number>` | `feat/<id>-...` |
| `TASK` | Work with no new user-facing behaviour: cleanup, data update, configuration, document, investigation | `docs/templates/04-final-task.md` | `TASK-<number>` | `task/<id>-...` |

- Follow the template's sections, in order, with nothing added or removed.
- If the type is unclear, decide from the table and say which you chose and why. If the user names a type, use it.
- Use the next free number across all types (look at the folder names in `docs/bugs/`), or the existing folder if the ticket already exists (then update its `04-final.md`).
- Title format `[type] title`, for example `[BUG] dashboard show wrong score number`. The ID is the folder name and is not part of the title.
- Do **not** create or edit `01-reported.md`, `02-analysis.md` or `03-discussion.md`. Those files, and the templates for them, are the user's own learning material. If they exist for this ticket, read them as input (the reporter's words, the answers) and leave them unchanged.

## 2. Steps

1. **Gather.** The user's description, plus any existing files in the ticket folder.
2. **Investigate** according to section 4 (reproduce a bug, look at the app for a feature, check what is touched for a task).
3. **Write** `04-final.md` with everything you verified. What is still unknown is written as a `(proposal)` the reader can accept or change, never as a fact. Keep the label `needs-info` while anything is unconfirmed, and use `env: to confirm` when the environment is unknown.
4. **Report back in your answer** (not in the file): the path, what you verified, what could not be reproduced or decided, and the numbered open questions for the reporter, each with your proposal. The file itself has no questions section.
5. **When answers arrive,** update `04-final.md` directly: fold each answer into the sections it changes, remove the `(proposal)` marks that were confirmed, and remove `needs-info` once nothing is left to ask. Never write an answer the reporter did not give.

## 3. Rules for every ticket

1. **Plain language only.** No code, file names, function names, stack traces, commits, branches, test names or technical terms (say "the page shows an error", not "ZeroDivisionError"; "one extra lookup per location", not "N+1"). Developers find the code themselves. Do not add a failing test or a technical section.
2. **Never invent facts.** Anything unknown (which page, which value, which environment, who owns it, what "done" means) is a `(proposal)` or marked "to be confirmed". Do not guess the environment.
3. **Name the page.** The Summary and the steps say which page or screen, and state plainly if it does not exist yet, or whether it is an existing page or a completely new one. There is no Where line, ID line or Status line in the ticket.
4. **Steps = user actions only.** No install, migrate, seed or run-server commands. If specific data must exist, say it inside the numbered steps with the real names and numbers (open this address, Riverside has 3 reviews rated 4, 5 and 2, look at this). There is no separate "Data needed" section.
5. **Exact results.** Give the real values or texts ("shows 3, should show 3.67") and the calculation if there is one.
6. **Labels (same set everywhere):** type (`bug`, `feature`, `task`); area (`dashboard`, `reviews-list`, ...); for bugs the kind (`crash`, `wrong-data`, `performance`, `ui`, `wrong-output`, optionally `intermittent`) and the reproduction result (`reproduced`, `partly-reproduced`, `cannot-reproduce`); `high-priority` only if urgent; `needs-info` while something is unconfirmed; `env: dev`, `env: staging`, `env: production` or `env: to confirm` (never guess; use `env: dev` for what you reproduced yourself locally, which is the dev environment); `deadline: <date>` only if one was given. Type line is just `Bug`, `New feature` or `Task`.
7. **Attachments:** list what exists and what is still to be added, never a file link.
8. **The ticket stands alone.** It never refers to another file, to the learning files, or to "above" or "below". It may mention other ticket IDs when they are related.

## 4. Rules per type

- **BUG:** Reproduce before you write. Run the app locally and follow your own steps. Before changing local data, back up `db.sqlite3` to the scratchpad and restore it afterwards. Fill Steps to reproduce, Expected result, Actual result and Environment with what you saw. If you could not reproduce it, say so and use the label `cannot-reproduce`. Never open files named `*DO-NOT-OPEN*`.
- **FEAT:** Look at the app first (read it, run it) and describe what exists today as a person sees it. Turn every undefined rule (what "good" means, what a "week" is, time zone, one location or all, filters combined or not, what to show when there is nothing) into an acceptance criterion marked `(proposal)`. Write acceptance criteria as "When <situation>, the screen must <result>", including the empty case. Check for other tickets that touch the same page and say how they relate.
- **TASK:** Say exactly what is touched, or "nothing visible to users". If users see a change, it is a FEAT; if something is broken, it is a BUG. Every "Done when" item must be checkable by a non-technical person. State what is in and out of scope.

## 5. Git naming (only when asked to create a branch or commit)

Follow CLAUDE.md: branch as in the table above, commit message `title`, blank line, `detail`, blank line, `Part of <id>`.

## 6. Before you finish

Re-read the ticket as a person who has never seen the code: do they know where, what, and how to follow the steps and see the same result? Then give the user the summary described in step 4.
