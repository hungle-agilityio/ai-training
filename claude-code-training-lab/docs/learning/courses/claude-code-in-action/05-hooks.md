# Lesson 5: Hooks

- **Course:** Claude Code in action (lesson 5 of 9, ~7 min)
- **Source:** https://academy.claude.com/courses/claude-code-in-action/hooks
- **Date:** 2026-10-20
- **Status:** In progress

The lesson has no exercises, no settings snippets and no hook code. These exercises are written for this lab and use the three hooks ReviewRadar already has (`.claude/hooks/`). Run them in Claude Code or the terminal, folder `claude-code-training-lab`. Do not change `.claude/settings.json` or any hook, do not commit, do not push. Where a hook is run by hand it only reads a JSON sample on stdin and prints an exit code. Proposals (Ex 5 to 7) are not applied; choosing to add a hook is a separate task with its own plan.

## Exercises

### Ex 1: Read a real hook

**Where:** Claude Code, read-only.

**Initial prompt:**
```
explain the commit hook
```

**Improved prompt:**
```
Read .claude/hooks/before-commit-check.py and the PreToolUse entry for it in .claude/settings.json. Answer with a table: (1) which event and matcher fires it, (2) what JSON it reads from stdin and which fields it uses, (3) every case where it exits with code 2, (4) what it does when it cannot check (does it fail closed or open), (5) which tests cover it in .claude/hooks/tests. Quote line numbers. Do not edit any file.
```

| Question | Your answer |
|---|---|
| Event and matcher in `settings.json`? | |
| Which stdin fields does the script read? | |
| How many different reasons can make it exit 2? | |
| Fails closed or open when it cannot check? | |

### Ex 2: Run a hook by hand, see the exit code

**Where:** Terminal, folder `claude-code-training-lab`. The hook reads the call as JSON on stdin and exits 0 (allow) or 2 (block, reason on stderr).

First ask Claude what JSON shape the hook expects (read-only):
```
Show me the exact JSON input that before-github-command-check.py expects on stdin, as one line I can pipe in. Do not run it.
```
Then, with the shape you found (the field names are in the script), try these commands as the `Bash` tool input and write the exit code and message:

| # | Command in the sample input | Expected | Exit code | Message |
|---|---|---|---|---|
| 1 | `git status` | allowed (0) | | |
| 2 | `gh issue list` | allowed (0) for the project repository | | |
| 3 | `gh repo list` | blocked (2) | | |
| 4 | `printenv GH_TOKEN` | blocked (2): reading the token | | |
| 5 | `curl https://github.com/someone-else/some-repo` | blocked (2): another repository | | |

Use only harmless sample strings. Do not run any real GitHub command through the hook, and do not pass a real token anywhere.

| Question | Your answer |
|---|---|
| Why does exit code 1 not block, while 2 does? (the lesson) | |
| What does Claude receive when a hook exits 2? | |
| How do you check the hook tests? (`uv run pytest .claude/hooks/tests -q --no-cov`) | |

### Ex 3: Watch a hook block Claude, from the inside

**Where:** Claude Code, permission mode **Manual**. Revert afterwards.

1. Make a trivial change (a blank line in a docstring).
2. Make sure you are on `main`: `git branch --show-current`.
3. Prompt:
```
Stage and commit the current change with the message "test commit".
```
4. Read exactly what the hook told Claude, and what Claude did next.

| Question | Your answer |
|---|---|
| Which hook stopped it, and which line of its message? | |
| What did Claude do after the block (explain, try another way, ask you)? | |
| Did it try to get around the block? (it should not; see `.claude/rules/security.md`) | |

Revert with `git checkout .` and make sure nothing was staged (`git status`).

### Ex 4: Exit 1 versus exit 2 (paper exercise)

| # | Hook returns | Blocks the tool call? | Why |
|---|---|---|---|
| 1 | exit 2 from a PreToolUse hook | | |
| 2 | exit 1 from a PreToolUse hook | | |
| 3 | exit 0 and JSON with `permissionDecision: "deny"` | | |
| 4 | exit 0 and JSON with `permissionDecision: "ask"` | | |
| 5 | exit 2 from a PostToolUse hook | | |
| 6 | exit 2 from a Stop hook | | |
| 7 | exit 2 from a SessionStart hook | | |

Expected: 1 yes (stderr goes to Claude); 2 no (stderr only logged, Claude continues); 3 yes (JSON decision); 4 no, hands the decision to you; 5 no (the tool already ran), but the text is fed back to Claude; 6 yes, Claude must keep working; 7 no, SessionStart ignores blocking and shows stderr only to the user.

Then answer: this project's hooks use exit 2. Why is that the right choice for a guard, and what could go wrong if one used exit 1 by mistake?

### Ex 5: Choose the event (paper exercise)

| # | Need | Event | Reason |
|---|---|---|---|
| 1 | Refuse any command that prints the token | | |
| 2 | Run `ruff format` after every Python file edit | | |
| 3 | Do not let Claude end its turn while the tests fail | | |
| 4 | Remind Claude of the open task after `/compact` | | |
| 5 | Log which CLAUDE.md and rule files were loaded | | |
| 6 | Check what a sub-agent returned | | |
| 7 | Replace a token-looking string in a command by a placeholder, then run it | | |

Expected: 1 PreToolUse; 2 PostToolUse; 3 Stop; 4 SessionStart with the `compact` matcher (PostCompact does not return output to the conversation); 5 InstructionsLoaded; 6 SubagentStop; 7 PreToolUse returning `updatedInput` instead of `deny`.

### Ex 6: Propose three hooks the project does not have (proposal only)

**Where:** Claude Code, read-only.

**Prompt:**
```
This project only has PreToolUse hooks. Propose three more, one at a time, without writing any file:
(a) a PostToolUse hook that runs ruff on a Python file right after Claude edits it,
(b) a Stop hook that runs ruff, mypy and pytest and blocks the turn from ending while they fail,
(c) a SessionStart hook with the compact matcher that prints the current branch, the open task and the files changed.
For each: the settings.json entry, the script in outline, the exit code or JSON it returns, what it costs per run, and how it could annoy me. Say which one is the least risky to try first.
```

| Hook | Event and matcher | Blocks? | Cost per run | Risk |
|---|---|---|---|---|
| (a) format or lint after edit | | | | |
| (b) tests at Stop | | | | |
| (c) re-inject state after compact | | | | |

| Question | Your answer |
|---|---|
| Which would you try first, and why? | |
| For (b): how many consecutive blocks should be allowed before it gives up? | |

### Ex 7: Redact instead of block (proposal only)

**Prompt:**
```
Explain the difference between a PreToolUse hook that denies a command containing a secret-like string and one that rewrites it with updatedInput. Write the JSON each would print for the command: echo sk_live_FAKEFAKEFAKE1234. Remember that updatedInput replaces the whole input object, so unchanged fields must be echoed back. Use only this fake string. Do not write any file.
```

| Question | Your answer |
|---|---|
| Which is better for this project, deny or rewrite? Why? | |
| What breaks if the rewrite forgets an unchanged field? | |
| Which is safer for commands that go to GitHub? | |

### Ex 8: Limits of hooks

**Where:** Read `.claude/hooks/README.md` ("Limits") and answer.

| Question | Your answer |
|---|---|
| What does a hook not see? (commands the user types, what a script does inside) | |
| When does a change to settings or hooks take effect? | |
| Which "never" rules in the README table are only text, and why can't a hook enforce them? | |
| For a run you are not watching, which rule would you most want to turn into a hook? | |

## Key takeaways

- **CLAUDE.md is a request, not a guarantee.** Hooks are deterministic code that runs at fixed points in the agentic loop, so they can enforce.
- **Events (about 30 per session; a few matter most):**

| Event | When | Typical use |
|---|---|---|
| PreToolUse | Before a tool call | Enforcement: can stop the call |
| PostToolUse | After a successful tool call | Auto-format, auto-lint |
| Stop | When Claude tries to end its turn | Refuse and keep Claude working (for example, until tests pass) |
| SubagentStop | When a sub-agent finishes | Check its result |
| PreCompact / PostCompact | Around compaction | Keep state |
| InstructionsLoaded | When a CLAUDE.md or rule file loads | Audit the context |
| SessionStart | Session start | Use `startup` for fresh starts; `compact` to re-inject context after compaction |
| UserPromptSubmit, UserPromptExpansion, Notification | Prompt or notice | Context or alerts |

- **Gotcha:** to re-inject context after compaction use SessionStart with the `compact` matcher. PostCompact does not return output to the conversation.
- **PreToolUse can return a decision as JSON** (print it to stdout and exit 0): `permissionDecision` is `allow`, `deny` or `ask` (`defer` only for non-interactive `-p` runs). `permissionDecisionReason` explains. `updatedInput` **rewrites** the call instead of blocking it, but it replaces the whole input object, so unchanged fields must be echoed back.
- **Exit codes for hooks without JSON:** `0` success (JSON on stdout is parsed; plain text is ignored on most events but added to context for SessionStart, UserPromptSubmit and UserPromptExpansion); `2` blocking error (stderr goes to Claude; blocks nearly every event, and can block Stop); **any other code, including 1, does not block** (stderr is logged and Claude continues). PostToolUse cannot stop a call that already ran, but can feed text back. Notification and SessionStart ignore blocking.
- **Matchers** pick the tool for PreToolUse (for example `Bash`); an optional `if` clause narrows it to a specific command.
- **Redact instead of block:** a hook can swap a live-looking secret for a placeholder with `updatedInput`, so the command still runs and the secret never passes through; `deny` would refuse outright.
- **Hooks turn "Claude usually listens" into "Claude can't skip it."** Guard tools with PreToolUse, gate the turn with Stop, preserve state with SessionStart (`compact`). The setup costs effort up front and pays off on runs you are not watching.
