# Lesson 2: Get started with the desktop app

- **Course:** Claude Code docs (lesson 2)
- **Source:** https://code.claude.com/docs/en/desktop-quickstart
- **Date:** 2026-10-20
- **Status:** In progress

All exercises use ReviewRadar as the project. Run them in the Claude desktop app, **Code** tab, environment **Local**, folder `claude-code-training-lab`. Do not commit; revert any change at the end with `git checkout .` (and `git clean -n` to see new files first).

## Exercises

### Ex 1: Open the Code tab and pick environment, folder and model

**Where:** Claude desktop app

**Steps:**
1. Open the app, click the **Code** tab (top centre).
2. In the row under the prompt box, click the environment selector and choose the top entry in the **Local** group.
3. Click the folder control, **Open folder…**, choose `claude-code-training-lab`.
4. Open the model picker (right end of the row) and note the models offered.

| Question | Your answer |
|---|---|
| Which layout do you have (environment selector under the prompt box, or the earlier layout)? | |
| Which environments are offered (Local, Cloud, SSH, WSL)? | |
| Which models does the picker list? | |
| Which permission mode is selected by default? | |

### Ex 2: Explore first, read-only

**Where:** Code tab, permission mode **Plan**. No files should change.

**Initial prompt:**
```
Find a TODO comment and fix it
```
Notice what the prompt does not say (which file, which TODO, how to test) and what Claude had to guess.

**Improved prompt** (new session):
```
Without changing any files: search reviews/ and .claude/ for TODO or FIXME comments. For each one give the file path and line, what it asks for, and whether it is safe to fix with a small change. If there are none, say so instead of inventing one.
```

**Check:** did Claude change anything? (The diff indicator `+N -N` must not appear.)

### Ex 3: Review a change in the diff view

**Where:** Code tab, permission mode **Manual**. Revert afterwards.

**Initial prompt:**
```
Add tests for the main function
```

**Improved prompt:**
```
Add one unit test for rounded_average in reviews/services.py that covers the half-up case (for example 3.25 -> 3.3). Put it in reviews/tests/unit next to the existing tests, follow the naming in .claude/context/conventions.md, and run only that test. Do not change any other file.
```
Then:
1. Click the `+N -N` indicator to open the diff view.
2. Comment on one specific line and see Claude revise.
3. Press **Reject** on one change and **Accept** on another.

| Question | Your answer |
|---|---|
| What did Manual mode ask before editing? | |
| What happened after you commented on a line? | |
| Did Claude ask before running the test command? | |

### Ex 4: Interrupt and steer, and give context with @

**Where:** Code tab. Revert afterwards.

**Prompt:**
```
Explain how the dashboard score is calculated. Start from @reviews/views.py and follow the calls down to the repository. Answer in 6 lines.
```
While it runs:
1. Type a correction ("also mention the time zone rule") and press **Enter** without stopping it.
2. In a second run, click the stop button and see what stays.

| Question | Your answer |
|---|---|
| Did the correction change the answer without a restart? | |
| What did `@filename` save you from typing? | |

### Ex 5: Permission modes side by side

**Where:** Code tab. Same small task in four modes. Revert after each run.

**Prompt (same in each mode):**
```
Add a docstring of one line to the first function in reviews/services.py that has none.
```

| Mode | Asked before editing? | Asked before running commands? | Changed a file? |
|---|---|---|---|
| Manual | | | |
| Accept edits | | | |
| Plan | | | |
| Auto (if offered on your plan) | | | |

### Ex 6: Slash commands and skills

**Where:** Code tab

Type `/` (or click **+** then **Slash commands**) and find:
- a built-in command,
- a project skill from `.claude/skills/` (for example `grill-me`),
- a project command from `.claude/commands/` (for example `/understand`).

Then run `/code-review` on a small change from Ex 3 before reverting it.

| Question | Your answer |
|---|---|
| Which project skills and commands appear in the list? | |
| Which ones are not in the list that you expected? | |
| What did `/code-review` report? | |

## Key takeaways

- The desktop app has three tabs: **Chat** (no file access), **Cowork** (autonomous background agent), **Code** (interactive coding with your local files). This lesson is about **Code**.
- The app includes Claude Code. You do not need Node.js or the CLI for the Code tab. A paid plan (Pro, Max, Team, Enterprise) is required.
- Environment: **Local** (a folder on your machine), **Cloud** (keeps running when the app closes), **SSH** (a remote machine), **WSL** (Windows only).
- Setup order in the row under the prompt box: environment, folder, model, then the task.
- Permission mode decides who approves: **Manual** asks for each edit and command, **Accept edits** applies file edits, **Plan** proposes without editing, **Auto** lets a background classifier block risky actions instead of asking you.
- The `+N -N` indicator opens the **diff view**: review file by file, comment on a line, Claude revises. Accept or Reject each change.
- Steer while it works: **Enter** sends a correction without stopping, the stop button interrupts at once.
- `@filename` pulls a file into the conversation. `/` lists built-in commands, project skills and plugin skills.
- More in the app: terminal (Ctrl+`), browser pane to preview the running app, parallel sessions with Git worktrees, side chat, scheduled tasks, pull request monitoring, connectors (GitHub, Slack, Linear).
- Same engine as the CLI: the lesson on the terminal and this one differ in the interface, not in what Claude can do.
