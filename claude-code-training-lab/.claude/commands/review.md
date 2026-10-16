---
description: Review the current diff before commit
---

Review the current changes (`git diff` and `git diff --cached`).

1. Use the `reviewer` sub-agent; it re-derives correctness from the issue and the code, not from the implementer's explanation.
2. Check against `.claude/rules/` and `.claude/knowledge/KNOWN_PITFALLS.md`.
3. Report findings by severity (blocker, should fix, nit) with `file:line`. For a pull request document use the `review-pull-request` skill instead.

Read-only: do not change code.
