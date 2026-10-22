# Lesson 1: Steering Long Sessions

- **Course:** Claude Code in action (lesson 1 of 9, ~6 min)
- **Source:** https://academy.claude.com/courses/claude-code-in-action/steering-long-sessions
- **Date:** 2026-10-20
- **Status:** In progress

The lesson has no exercises of its own. These exercises are written for this lab and use ReviewRadar. Run them in Claude Code, folder `claude-code-training-lab`. Do not commit and do not push; revert each change before the next exercise with `git checkout .` (and `git clean -n` to see new files first).

## Exercises

### Ex 1: Scope with plan mode, then read and correct the plan

**Where:** Claude Code, plan mode (`Shift+Tab` until `⏸ plan mode on`, or `claude --permission-mode plan`).

**Initial prompt:**
```
add a minimum rating filter to the reviews page
```

**Improved prompt:**
```
Plan a "minimum rating" filter (1 to 5) on the reviews page. Research first: read reviews/forms.py, reviews/services.py, reviews/repositories.py, reviews/views.py and the existing filter tests. Then give the plan as numbered steps with the file for each, the tests (including the query count), and what is out of scope. Do not edit any file.
```
Read the plan and send one correction (for example: "the form must reject 0 and 6", or "add the template change"). Compare the plan before and after your correction.

| Question | Your answer |
|---|---|
| What was missing from the first plan? | |
| How many corrections did the plan need before you would approve it? | |
| Which would have been more expensive: fixing the plan, or fixing the code after a wrong run? | |

### Ex 2: Directed compaction

**Where:** Claude Code. Needs a session with some history: do Ex 1 first, or ask two or three questions about `reviews/`.

**Initial prompt:**
```
/compact
```

**Improved prompt** (a second session with the same history):
```
/compact Focus on the minimum rating filter: the files to change, the tests to write and the rule that ratings are 1 to 5. Drop the exploration of other files.
```
After each, ask:
```
What do you remember about the plan? List the files and the tests.
```

| Question | Your answer |
|---|---|
| What did the plain `/compact` lose or blur? | |
| What did the directed `/compact` keep? | |
| Did Claude drift (change the plan) after compacting? | |

### Ex 3: Rewind menu, all five options

**Where:** Claude Code, permission mode **Accept edits**. Revert afterwards.

1. Prompt: `Add a one-line docstring to the first function in reviews/services.py that has none.`
2. Prompt: `Now add a one-line docstring to the next function that has none.`
3. On an empty prompt press `Esc Esc` to open the rewind menu and try each option on a checkpoint:

| Option | What you do | What changed (code, conversation) |
|---|---|---|
| Restore code and conversation | Go back to before step 1 | |
| Restore conversation | Pick the checkpoint after step 1 | |
| Restore code | Pick the checkpoint after step 1 | |
| Summarize from here | Pick the checkpoint after step 1 | |
| Summarize up to here | Pick the checkpoint after step 2 | |

**Check:** run `git status` and `git diff` after each restore. Then run a shell command through Claude (for example `Create an empty file out-test.txt with the shell`) and rewind the code: is the file removed? (Checkpoints do not track shell changes. Delete the file yourself.)

### Ex 4: Set a goal Claude can finish alone

**Where:** Claude Code, permission mode **Accept edits** (or the sandbox if you use it). Revert afterwards.

**Initial prompt:**
```
make the tests better
```

**Improved prompt:**
```
/goal uv run pytest -q --no-cov passes, uv run ruff check . reports no errors, and uv run mypy . reports no errors, after you add one unit test in reviews/tests/unit for each public function in reviews/services.py that has no test. Print the output of the three commands in your last message.
```
Watch it work across turns, then clear it:
```
/goal clear
```

| Question | Your answer |
|---|---|
| How many turns did it run before the evaluator accepted? | |
| Why does the condition ask to print the command output? (The evaluator only reads the transcript.) | |
| Write one goal that would be too vague to evaluate, and why: | |

### Ex 5: Loop to poll something external

**Where:** Claude Code. Needs a pull request or a workflow run on GitHub. Read-only: do not push or create anything on GitHub. If there is no run to watch, do the paper part only.

**Prompt (self-paced loop):**
```
/loop check the latest run of the checks workflow on the repository with gh run list --limit 1 and tell me when its status changes to completed. Stop when it is completed.
```
Press `Esc` to stop a self-paced loop while it waits.

| Question | Your answer |
|---|---|
| What interval did Claude choose when you gave none? | |
| How long does a fixed-interval loop run if you never cancel it? (seven days) | |
| What is a loop better for than a scheduled task? | |

### Ex 6: Parallel work with worktrees

**Where:** Terminal (two windows), repository `ai-training`.

```bash
claude --worktree filter-min-rating
claude --worktree docstrings
```
In each, ask for a different small change in different files. Then in a third window:
```bash
git worktree list
```
Exit one session without changes and check that its worktree is removed automatically; keep the other one with a change and note what stays.

Then ask Claude (proposal only, do not create the file):
```
Which git-ignored files does this project need in a fresh worktree to run the tests (for example .env or db.sqlite3)? Propose the content of a .worktreeinclude file at the repository root. Do not create it.
```

| Question | Your answer |
|---|---|
| Where is each worktree created and on which branch? | |
| What was removed on exit, and what stayed? | |
| Which files did Claude put in the proposed `.worktreeinclude`? Do any of them hold secrets? | |

### Ex 7: Choose the tool (paper exercise)

| # | Situation | Tool | Reason |
|---|---|---|---|
| 1 | A change touches the form, service, repository and view; you are not sure of the approach | | |
| 2 | Claude is 40 turns in and starts to forget the test command | | |
| 3 | Claude changed three files and the last one is wrong; the first two are fine | | |
| 4 | You can say "all tests green" better than you can list the steps | | |
| 5 | You want to know when the CI run finishes and then act | | |
| 6 | Two features in the same repository, at the same time | | |

Expected: 1 plan mode; 2 `/compact` with a focus; 3 rewind, restore code to the checkpoint; 4 `/goal`; 5 `/loop`; 6 worktrees.

## Key takeaways

- Long tasks need two habits: **scope before** Claude starts, and **steer while** it runs.
- **Plan mode:** Claude researches and plans without editing source files. Read the plan, add what is missing, correct what is off. Fixing a plan is cheaper than cleaning up after a wrong run.
- **`/compact`:** summarizes the conversation and replaces the old messages to free the context window. Details can be lost and Claude can drift, so direct it: `/compact Focus on the --version flag implementation`.
- **Rewind:** every prompt makes a checkpoint. `Esc Esc` on an empty prompt opens the menu: restore code and conversation, restore conversation, restore code, summarize from here, summarize up to here.
- **`/goal`:** a completion condition. Claude keeps working across turns until a fast evaluator confirms it. The evaluator reads only the transcript, so the condition must be checkable from Claude's output (test results, command output). `/goal clear` cancels.
- **`/loop`:** runs a prompt on an interval (fixed or self-paced) to poll outside state such as a CI run or a deploy. `Esc` stops a self-paced loop; a fixed-interval loop runs until cancelled or seven days pass.
- **Worktrees:** each session gets its own file tree, so parallel agents cannot overwrite each other. A clean worktree is removed when its session exits. `.worktreeinclude` at the repository root lists git-ignored files (local config, environment files) to copy into every worktree.
- Summary of the lesson: scope first, then steer; direct your compaction; rewind when Claude drifts; set a goal when you can describe "done" better than the steps; run parallel work in worktrees.
