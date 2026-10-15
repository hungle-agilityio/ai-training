---
description: Execute an approved plan, test first
argument-hint: <ticket number or folder>
---

Implement the approved plan for: $ARGUMENTS

1. Confirm Gate 1 was passed. If there is no approved plan (and the ticket is not Easy), stop and ask.
2. Use the `implementer` sub-agent. It follows the plan step by step, test first, and builds only what the plan says. A change of scope goes back to `/plan`.
3. Work on the ticket's branch (`.claude/rules/git.md`), never on `main`.
4. Finish with `/test` and report what changed.
