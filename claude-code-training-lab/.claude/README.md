# .claude: map of this folder

```
.claude/
├── CLAUDE.md        entry point: index and always-on limits
├── rules/           MUST-follow rules, loaded automatically
├── context/         background knowledge, imported by CLAUDE.md
├── knowledge/       growing store (business rules, pitfalls, ADRs), NOT auto-loaded
├── skills/          how to do a topic (write-issue, create-commit, create-issue, create-pull-request, review-pull-request, write-tests, diagnose-bug, grill-me)
├── templates/       code skeletons (not the issue templates in docs/app/templates)
├── commands/        slash commands for each lifecycle step
├── agents/          sub-agents with a role and a model (analyst, planner, implementer, reviewer, test-runner)
├── hooks/           guard that runs before every shell command (one repository only)
└── settings.json    permissions
```

## Lifecycle by difficulty

| Difficulty | Steps |
|---|---|
| Easy | `/understand` → code → `/test` → Gate 2 (human) → `/commit` |
| Medium | `/understand` → `/plan` → Gate 1 (human) → `/implement` → `/test` → `/review` (if a trigger applies) → `/verify` → Gate 2 (human) → `/commit` |
| Hard | `/understand` → `/plan` (maybe split) → Gate 1 (human) → `/implement` → `/test` → `/review` → `/verify` → Gate 2 (human) → `/learn` → `/commit` |

Gates and triggers: `rules/workflow.md`.
