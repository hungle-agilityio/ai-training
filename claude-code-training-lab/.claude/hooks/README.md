# Hooks: guards that run before shell commands

A hook is a small program that the harness runs before a shell command (or a tool call such as publishing an artifact) that Claude wants to run. If it exits with code 2 the command does not run and Claude gets the reason. Anything that must always hold is a hook or a permission rule, not a sentence Claude reads.

| Hook | Refuses |
|---|---|
| `before-github-command-check` | `gh`, `git`, `curl` and `ssh` commands that reach a GitHub repository other than the one in `github-allowed-repo.txt`; commands that manage repositories, accounts or secrets; reading or printing the token (`GH_TOKEN`, `printenv`, `env`) |
| `before-commit-check` | Staging the database file, secrets files and caches (also with `--force`); a commit with those staged, with a secret-like string in the staged lines, with an attribution line in the message (Co-Authored-By, Generated with), on `main`, or while lint or types fail |
| `before-artifact-publish` | Publishing a file under `out/verify/` with the Artifact tool unless the sharing gate allows it (masking `clean`, standing approval `on`, size under the limit) |

All fail closed: if a hook cannot check a command that looks relevant, the command is blocked. Their tests are in `tests/` and run in the automatic checks.

## Each "never": where it is enforced

| Never | Enforced by |
|---|---|
| Commit on `main` | `before-commit-check` |
| An attribution line in a commit | `before-commit-check` |
| Stage `db.sqlite3`, `.env`, keys, caches | `before-commit-check` |
| Commit a secret | `before-commit-check` (known token shapes only) |
| Commit while lint or types fail | `before-commit-check` |
| Force-push, `--no-verify`, `reset --hard` | `permissions.deny` |
| Push without approval | `permissions.ask` (`git push`) |
| Open a pull request without approval | `permissions.ask` (`gh pr create`) |
| Merge, approve or comment on a pull request, delete an issue or a repository | `permissions.deny` |
| Publish a report that is not masked | `before-artifact-publish` and `.claude/skills/share-report/rules.md` |
| Touch another GitHub repository | `before-github-command-check` and the limited token |
| Read or print the token | `before-github-command-check` |
| Read `.env` files | `permissions.deny` (`Read`) |
| Open files named `*DO-NOT-OPEN*` | `permissions.deny` (`Read`) |
| Amend or rebase pushed commits | `permissions.ask` (`git rebase`); amending is text only |
| Delete data nobody asked to delete, invent facts, widen the scope, change the requirement | Text and review only: judgement, not a command |

## Limits

- `before-artifact-publish` has 15 tests of its logic and was seen firing on the first real publish (an `allowed` line in `out/artifact-publish.log`). A call that the Artifact tool rejects first, for example for a missing file, never reaches the hook. A live `blocked` case has not been triggered on purpose, because it would need a publish to be attempted.
- A hook sees only the shell commands that Claude runs. It does not see what a script run by Claude does inside, and it does not see commands the user types.
- A change of settings or hooks needs a new session to take effect.
- The secret scan knows a few token shapes (GitHub, AWS, Slack, `sk-`, private keys). It is a net, not a proof.
- Checks run in the nearest folder that holds `pyproject.toml`, and they take a few seconds on every commit.
