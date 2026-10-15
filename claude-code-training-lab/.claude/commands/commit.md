---
description: Draft a commit message from the diff and commit it in the project format
---

Confirm Gate 2 (the user checked the verified result and said OK). If not, stop and ask.

Use the `git` skill to commit the current changes.

- Format and branch rules: `.claude/rules/git.md`. Never commit to `main`.
- Group the changes into commits by purpose; stage files by name.
- Message: title, detail, `Part of #<id>` when there is a ticket. No `Co-Authored-By` and no "Generated with" line.
- Show me the message and the files first if the split is not obvious. Do not push.
