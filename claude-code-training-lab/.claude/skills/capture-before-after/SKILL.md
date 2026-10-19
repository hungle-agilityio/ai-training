---
name: capture-before-after
description: Capture the same browser steps before and after a change, on the same demo data and window size, and pair the screenshots with a label (changed, no visible difference, did not exist before). Use for any issue that changes what users see, for the pull request evidence, or when the user asks for before and after images.
---

# Capture before and after

A reviewer should see what changed without running the app. This skill runs the same steps on the base of the change and on the current work, and lays the two screenshots side by side.

## Run it

```
uv run python .claude/skills/capture-before-after/before_after.py [--base <ref>] [--spec <file>]
```

- `--base` is the "before": any git ref. Without it, the merge base with `main` is used; while `main` does not hold the project yet the program stops and asks for `--base`.
- The base is checked out in a **temporary git worktree** that is removed afterwards, so the working folder is never touched. Both sides run on a throw-away demo database with the same window size (1280 by 800) and the same steps, through the `check-in-browser` program.
- Steps come from `--spec` (the same format as for `check-in-browser`: write them from the issue's "Steps to check the result"); the default is the dashboard and the reviews pages.
- Output in `out/before-after/<time>/` (git-ignored): `before/` and `after/` screenshots, `compare.html` (side by side, self-contained) and `compare.json`.

## Read the labels

| Label | Meaning |
|---|---|
| `changed` | the two screenshots differ |
| `no visible difference` | identical screenshots: say so, do not present them as evidence of a change |
| `did not exist before` | the page answered 404 at the base and exists now (a new page) |
| `not captured before` / `not captured after` | a step ran on one side only |

## Rules

- The images show demo data only. The same masking scan as in `check-in-browser` runs on both sides: if personal data is found the run stops (exit code 3) and `compare.json` says `masking: findings`. Do not publish or attach the images unless it says `clean`.
- When the base cannot be built (a missing dependency, a broken commit), report `NOT RUN` and the reason; never fake the "before".
- A change that users cannot see has no before and after: say "nothing visible to users" instead.
