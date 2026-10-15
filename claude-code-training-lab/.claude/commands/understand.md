---
description: Evidence-first analysis of a ticket, then classify difficulty
argument-hint: <ticket number, folder or pasted report>
---

Analyse the ticket: $ARGUMENTS

1. Use the `ticket-analyst` sub-agent. It reads the ticket, the code and `docs/reviewradar-project-context-2026-10.md`, and checks `.claude/knowledge/` for known rules and pitfalls.
2. Relay its questions to me, numbered, each with a proposal I can accept.
3. After my answers, give the difficulty (Easy, Medium or Hard) and the steps from `.claude/rules/workflow.md`.

Do not change code or tickets in this step.
