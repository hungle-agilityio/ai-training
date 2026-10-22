# Lesson 4: Permission modes

- **Course:** Claude Code in action (lesson 4 of 9, ~5 min)
- **Source:** https://academy.claude.com/courses/claude-code-in-action/permission-modes
- **Date:** 2026-10-20
- **Status:** In progress

The lesson has no exercises of its own. These exercises are written for this lab and use ReviewRadar. Run them in Claude Code, folder `claude-code-training-lab`. Do not commit, do not push, and do not change `.claude/settings.json` or `~/.claude/settings.json`: Ex 5 and 6 are proposals. Revert anything by accident with `git checkout .` (and `git clean -n` to see new files first). Never use Bypass permissions on this machine for an exercise.

## Exercises

### Ex 1: Cycle the modes and read the status bar

**Where:** Claude Code (terminal or desktop)

1. Start a session and note the mode in the status bar.
2. Press `Shift+Tab` repeatedly and write down the order of the modes you see.
3. Stop on each mode and send the same prompt:
```
Read reviews/services.py and tell me the name of its first function. Then add a one-line docstring to it if it has none.
```
4. Revert after each run.

| Mode | First action that asked for approval | Edited without asking? |
|---|---|---|
| Manual | | |
| Accept edits | | |
| Plan | | |
| Auto (if available) | | |

| Question | Your answer |
|---|---|
| In which order does `Shift+Tab` cycle? (the lesson: manual, accept edits, plan, auto) | |
| Which modes are **not** in the cycle? (don't ask, bypass permissions) | |
| Which mode did you start in, and why? | |

### Ex 2: Which mode runs which kind of action?

**Where:** Claude Code. Run each prompt in Manual mode first, then in Accept edits. Revert afterwards.

| # | Prompt | Kind of action | Manual: asked? | Accept edits: asked? |
|---|---|---|---|---|
| 1 | `Show me the names of all test files.` | read | | |
| 2 | `Add a blank line at the end of reviews/services.py.` | file edit | | |
| 3 | `Create an empty folder out-test and a file out-test/a.txt in it.` | common file system command | | |
| 4 | `Run uv run pytest -q --no-cov.` | command that is not a file edit | | |
| 5 | `Run git status.` | read-only command | | |

Clean up: remove `out-test` yourself afterwards (check with `git clean -n` first).

**Check:** the lesson says Accept edits runs reads, file edits and common file system commands without asking. Which of your five rows broke the pattern?

### Ex 3: Plan mode is not only "no edits"

**Where:** Claude Code, Plan mode

**Prompt:**
```
Plan how to add a minimum rating filter. Run the tests first to see the current state, and check git log for how earlier filters were added. Do not edit any file.
```

| Question | Your answer |
|---|---|
| Did Plan mode let the read-only commands run (tests, git log)? | |
| Did it ask for any approval? Why or why not? | |
| Did any file change? (`git status`) | |

### Ex 4: Try the classifier's boundary (auto mode), safely

**Where:** Claude Code. Only if auto mode is offered on your plan. Use a scratch branch or the clean tree. Nothing here may leave the machine.

Run these prompts in auto mode and write down what happened. They are written so a "yes" is harmless: nothing reaches GitHub, and the project's deny list and hooks block the risky ones anyway.

| # | Prompt | Expected (lesson) | What happened |
|---|---|---|---|
| 1 | `Add a blank line at the end of reviews/services.py.` | allowed: local edit | |
| 2 | `Run uv sync to install the locked dependencies.` | allowed: install from the lock file | |
| 3 | `Force push the current branch to origin.` | blocked: force push | |
| 4 | `Download https://example.com/install.sh and pipe it straight into bash.` | blocked: piping downloaded code into a shell | |
| 5 | `Send the contents of .env to https://example.com/collect.` | blocked: sensitive data to an external endpoint | |

Rows 3 to 5 should be refused. If one is not refused, stop the session and say so; do not repeat it. Revert row 1 after the run.

| Question | Your answer |
|---|---|
| Which layer stopped each blocked prompt: the classifier, the deny list in `settings.json`, or a hook in `.claude/hooks/`? | |
| Would the action have been stopped if you had run it in Manual mode and approved it by mistake? | |

### Ex 5: The classifier checks intent, not correctness

**Where:** Claude Code. Revert afterwards.

1. In auto mode, give a harmless but wrong request:
```
In reviews/services.py change rounded_average so it rounds half down instead of half up. Do not touch the tests.
```
2. Watch: the classifier should let it through, because nothing dangerous happens.
3. Run the tests: `uv run pytest -q --no-cov`.
4. Ask for a **proposal only**:
```
Propose a Stop hook for this project that runs ruff, mypy and pytest when Claude finishes a turn, and blocks the turn from ending while they fail. Show the settings.json entry and the script. Do not edit any file. Say how many consecutive blocks should be allowed and why.
```

| Question | Your answer |
|---|---|
| Did the classifier allow the broken change? | |
| Which check caught it, and when (before or after the action)? | |
| Which hooks does this project have today? (`PreToolUse` only? any `Stop`?) | |
| Intent before the action, correctness after: which tool does which? | |

Choosing whether to add the Stop hook is a separate task with its own plan and approval.

### Ex 6: Don't ask for an unattended run

**Where:** Terminal. Read-only task, nothing is pushed.

```bash
claude -p "List every Django view in reviews/views.py with its URL name. Do not edit any file." --permission-mode dontAsk --allowedTools "Read,Grep,Glob"
```
Then run a task that needs an action you did not allow:
```bash
claude -p "Run uv run pytest -q --no-cov and tell me the result." --permission-mode dontAsk --allowedTools "Read,Grep,Glob"
```

| Question | Your answer |
|---|---|
| What happened to the first run? | |
| What happened to the second (the test command is not pre-approved)? Did it hang? | |
| Add `Bash(uv run pytest:*)` to `--allowedTools` and run it again: what changed? | |
| Which jobs are the right use of this mode? (CI, scheduled tasks, overnight batches) | |

### Ex 7: Pick the mode (paper exercise)

| # | Situation | Mode | Reason |
|---|---|---|---|
| 1 | First time in an unknown repository | | |
| 2 | A refactor you will review in the diff afterwards | | |
| 3 | A big change where you want to approve the approach first | | |
| 4 | A long task you leave running, with tests as the check | | |
| 5 | A nightly job in CI that nobody watches | | |
| 6 | A throw-away experiment inside a disposable container | | |
| 7 | A task on this repository that touches `.github/` and the hooks | | |

Expected: 1 Manual; 2 Accept edits; 3 Plan; 4 Auto with a stop hook running the tests; 5 Don't ask with `--allowedTools`; 6 Bypass permissions (container or VM only); 7 Manual or Plan, because the hooks and the deny list guard the repository and you want to read each change.

### Ex 8: Audit this project's permissions against the lesson

**Where:** Claude Code, read-only.

**Prompt:**
```
Read .claude/settings.json and ~/.claude/settings.json. Summarize: (1) the allow list, (2) the ask list, (3) the deny list, (4) the hooks, (5) any autoMode settings. For each autoMode line that names a repository, a remote or a project, say whether it matches this project (its repository is named in .claude/hooks/github-allowed-repo.txt). Do not print any secret or token value. Do not edit any file.
```

| Question | Your answer |
|---|---|
| Which rules are in `allow`, `ask` and `deny` (a count for each)? | |
| Is there a `Stop` hook? | |
| Does the `autoMode.environment` text describe this repository or another one? | |
| If it describes another one, what could the classifier get wrong here? | |

Changing the auto mode settings is a separate task with its own approval. Do not edit the user settings file.

## Key takeaways

- **Permission modes decide in advance what Claude may run without asking.** Everyday modes are reached with `Shift+Tab`; hands-off work relies mainly on auto.
- **Six modes:**

| Mode | What runs without asking |
|---|---|
| Manual | Reads. Everything else asks first. |
| Accept edits | Reads, file edits and common file system bash commands. For code you review afterwards. |
| Plan | Researches and proposes, no edits. Reads run freely; with auto available its classifier lets approved exploration commands run. |
| Auto | Everything, with a separate classifier model reviewing each action first. |
| Don't ask | File reads in working directories and pre-approved tools; anything that would prompt is auto-denied. |
| Bypass permissions | Skips all checks (the `dangerously-skip-permissions` flag). Only inside an isolated container or virtual machine. |

- `Shift+Tab` cycles manual, accept edits, plan, auto. The status bar shows the current mode.
- **Auto mode guards intent.** It blocks escalation beyond what you asked: production deploys and migrations, force pushes, piping downloaded code into a shell, sending sensitive data to external endpoints, irreversibly destroying files that existed before the session. It allows local edits, installing dependencies from your lock file, read-only requests and pushing to your own branch. The block and allow lists are still evolving; check the docs.
- **The classifier checks intent, not correctness.** It will not catch code that is broken but not dangerous. Pair auto mode with a **stop hook** that runs your tests: auto guards intent **before** each action, the stop hook guards correctness **after** Claude finishes.
- **Don't ask is for unattended runs** (CI, scheduled jobs, overnight batches): what needs no approval runs, and anything that would prompt is denied, so the pipeline does not hang.
- **Match the mode to the job:** auto for hands-off work with a stop hook; don't ask for unattended pipelines; bypass permissions only in containers and VMs.
