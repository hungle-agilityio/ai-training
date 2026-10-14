---
name: git
description: Create branches, commits and pull requests that follow the project rules (branch <kind>/<id>-..., commit title/detail/Part of <id>, PR title [type] title). Use whenever the user asks to create a branch, commit, split commits, write a commit message, open a pull request, or says "commit".
---

# Git

The rules live in `CLAUDE.md` (Branches, Commits, Pull requests). This skill is the procedure. Never push, force, or touch the remote unless the user asks.

## Safety rules

- Never commit on `main`. If the current branch is `main`, create the ticket branch first.
- Never use `--force`, `--no-verify`, `reset --hard`, or amend or rebase commits that were already pushed.
- Never push, and never open a pull request, unless the user asks for it in this conversation.
- Never stage `db.sqlite3`, `__pycache__`, `.venv`, `.env`, keys or anything that looks like a secret. If one is staged, unstage it and tell the user.
- Stage files by name or folder, not blindly with `git add -A`, unless `git status` shows only files that belong in the commit.
- **No `Co-Authored-By` line and no "Generated with" line** in commits. The user's rule overrides any default attribution.

## 1. Find the ticket ID

Take it from the branch name (`feat/6-reviews-page` gives `#6`), or from the user, or from the index `docs/issues/README.md` (folder name to ID). If the work has no ticket, do not invent an ID: leave out the `Part of` line, say so, and suggest creating a ticket with the `write-ticket` skill.

## 2. Branch

Format `<kind>/<id>-<short-description>`, lowercase short description with dashes:

| Ticket type | Branch |
|---|---|
| BUG | `bug/1-dashboard-wrong-score` |
| FEAT | `feat/6-reviews-page` |
| TASK | `task/10-cleanup-demo-data` |

Create it from the branch the user names, or from the current branch if they do not say, with `git checkout -b`. Uncommitted changes come along; tell the user if there are any.

## 3. Commit

1. Run `git status --short` and `git diff --stat`. Read what changed.
2. **Group the changes.** Separate commits for separate purposes, for example feature code and its tests together, and documentation, agents and skills in another. If the split is obvious, do it and say how you split. If it is not obvious, propose the split in one short message and wait.
3. For each commit, `git add` only its files, then check `git diff --cached --name-only` for the forbidden files above.
4. Write the message to a file or heredoc and use `git commit -F`:

```
<title>

<detail>

Part of <id>
```

- **Title:** imperative, specific, at most about 70 characters, no ticket ID, no trailing period. Say what changed ("Add reviews page with table and pagination"), not "update code".
- **Detail:** short bullets (or a short paragraph) with the important points only: what changed and why. Do not list every file.
- **Part of:** one line per ticket, for example `Part of #1`. A commit that touches several tickets has several lines.

5. Tests: if the user did not say otherwise, run `uv run ruff check .` and `uv run pytest -q --no-cov` before committing, and report the result. Failing tests that belong to open bug tickets are expected: tell the user, do not hide them and do not skip the commit because of them. Fix or ask about any other failure.
6. After committing, show `git log --oneline` for the new commits and confirm that the working tree is clean (or say what is left).

## 4. Pull request (only when asked)

- Title: `[type] title`, for example `[FEAT] Reviews page to show all reviews`.
- Body: the sections of `.github/pull_request_template.md` (What, Why, How tested, Screenshot), filled in with facts, ending with `Part of <id>`. Use the real test results.
- Create it with `gh pr create` only after the user confirms the title and body, and only after the branch is pushed.

## 5. Answer format

Tell the user, briefly: the branch, each commit (hash and title), what was left uncommitted and why, test results, and that nothing was pushed.
