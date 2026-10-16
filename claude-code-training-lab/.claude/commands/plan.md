---
description: Produce the step-by-step, test-first plan for an analysed ticket
argument-hint: <ticket number or folder>
---

Plan the ticket: $ARGUMENTS

1. Use the `planner` sub-agent on the analysed ticket (Medium and Hard only; Easy tickets skip this).
2. The plan follows `.claude/rules/architecture.md` and, if useful, `.claude/templates/layered-feature.md`. It checks `.claude/knowledge/BUSINESS_RULES.md` and `KNOWN_PITFALLS.md`.
3. Show me the plan and **stop at Gate 1**: wait for my approval before any code is written.
