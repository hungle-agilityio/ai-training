# Lesson 1: Quickstart

- **Course:** Claude Code docs (lesson 1)
- **Source:** https://code.claude.com/docs/en/quickstart
- **Date:** 2026-10-20
- **Status:** In progress

All exercises use ReviewRadar as the project. Run them in a terminal from the folder `claude-code-training-lab`. Do not commit; revert any change at the end with `git checkout .` (and `git clean -n` to see new files first).

## Exercises

### Ex 1: Check the install and start a session

**Where:** Terminal

Claude Code is already installed, so this is a check, not an install.

**Steps:**
```bash
claude --version
cd /Users/hungle/hungle/training/ai-training/claude-code-training-lab
claude
```
Inside the session, type `/help`, then `/resume` (look, then cancel), then `/exit`.

**Expected:** the version number followed by `(Claude Code)`; the prompt shows the version, the model and the working directory.

| Question | Your answer |
|---|---|
| Which version is installed? | 2.1.304 |
| Which account type are you logged in with? (`/login` shows it) | |
| What does `/resume` list? | |

### Ex 2: Ask the first questions

**Where:** Claude Code, folder `claude-code-training-lab`. Read-only: no files should change.

**Initial prompt:**
```
what does this project do?
```

**Improved prompt:**
```
Without changing any files: (1) what does ReviewRadar do, in 3 lines; (2) which technologies does it use, as a table; (3) where is the entry point of the Django app; (4) the folder structure in 8 lines. Quote file paths. If something is unclear, say so instead of guessing.
```

Then ask about Claude Code itself:
```
what can Claude Code do in this repo, and how do I create a custom skill? List the skills this project already has.
```

**Check:** compare the answers with `README.md` and `.claude/skills/`. Did Claude read files it needed without you adding context?

### Ex 3: First code change and permission modes

**Where:** Claude Code. Revert afterwards.

**Initial prompt** (permission mode: Manually approve):
```
add a hello world function to the main file
```
Note what Claude had to guess ("the main file"), and what it asked you before editing.

**Improved prompt** (press `Shift+Tab` to switch to Plan mode first):
```
Propose where a small helper `greeting(name: str) -> str` should live in reviews/ according to the project rules in .claude/CLAUDE.md, with a test next to the others. Type hints are required. Do not change any files yet.
```
Then approve the plan, switch to Accept edits with `Shift+Tab`, and let it implement. Run the tests, then revert.

**Check:** which action asked for approval in each mode? Write it in the table below.

| Mode | Asked before editing? | Asked before running a command? |
|---|---|---|
| Manually approve | | |
| Plan | | |
| Accept edits | | |

### Ex 4: Git in plain language

**Where:** Claude Code, after Ex 3 (there are changes to look at). Do not let it commit.

**Initial prompt:**
```
what files have I changed?
```

**Improved prompt:**
```
Show the files I changed as a table (file, what changed in one line). Then show the last 5 commits. Then write a commit message for these changes that follows .claude/rules/git.md, but do NOT run git commit.
```

**Check:** does the proposed message follow the repo rules (no `Part of` line without an issue number, no Co-Authored-By)? Does the commit hook in `.claude/hooks/` match what you expect?

### Ex 5: Shell commands

**Where:** Terminal

| Command | Try | Result |
|---|---|---|
| `claude "task"` | `claude "list the skills in .claude/skills"` then `/exit` | |
| `claude -p "query"` | `claude -p "explain what .claude/hooks/before-commit-check.py does in 3 lines"` | |
| `claude -c` | continue the last conversation | |
| `claude -r` | pick an older conversation | |
| `/clear` | inside a session | |

## Key takeaways

- The Quickstart is seven steps: install, first session, first question, first code change, Git, fix or add a feature, other workflows.
- Install with the native installer (`curl -fsSL https://claude.ai/install.sh | bash`) or Homebrew (`brew install --cask claude-code`). Native updates itself; Homebrew and WinGet do not.
- Start with `cd project` then `claude`. The first run asks you to log in; `/login` switches accounts later.
- Claude Code reads files as it needs them. You do not add context by hand, but a specific request still gives a better result.
- **Permission mode** decides what Claude can do without asking. `Shift+Tab` cycles the modes in the running session.
- Git is conversational: status, branches, history, commit messages, merge conflicts. Approve the commit yourself.
- Shell commands: `claude`, `claude "task"`, `claude -p "query"` (one-off, then exit), `claude -c` (continue last), `claude -r` (resume a choice).
- Session commands: `/help`, `/clear`, `/exit` (or Ctrl+D twice), `/resume`, `/login`. Type `/` to list commands and skills; Tab completes; ↑ is history.
- Tips: be specific ("fix the login bug where users see a blank screen after wrong credentials", not "fix the bug"); give numbered steps for big work; let Claude explore before it changes anything.
- Next pages: how Claude Code works, best practices, common workflows, extending Claude Code (CLAUDE.md, skills, hooks, MCP).
