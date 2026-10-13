# claude-code-training-lab

## Goals

Learn Claude Code by building **ReviewRadar**: collect and respond to customer reviews for a multi-branch business.

- **Business:** online reputation management.
- **MVP:** import reviews (CSV / mock API), classify sentiment with the Claude API, suggest replies, score dashboard per branch.
- **Learning focus:** real LLM integration, caching, multi-branch business modeling.

## How to run

```bash
uv venv
uv pip install -r requirements.txt
uv run python manage.py migrate
uv run python manage.py seed_demo_data
uv run python manage.py runserver
uv run pytest
```

Open http://127.0.0.1:8000/dashboard/ for the branch scores.

`seed_demo_data` wipes the local DB tables and creates demo data. Options:
`--branches N` (extra branches) and `--with-new-branch` (a branch with no reviews).

## Bug tickets

Tickets live in `docs/bugs/`. Copy `_template.md` structure when writing a repro-ready report.

## 15-Day Progress

| Day | Topic | Status |
|-----|-------|--------|
| 1 | | ☐ |
| 2 | Bug seed tickets | ☐ |
| 3 | | ☐ |
| 4 | .claude/ | ☐ |
| 5 | CLAUDE.md | ☐ |
| 6 | Subagent | ☐ |
| 7 | Slash command, skill | ☐ |
| 8 | MCP | ☐ |
| 9 | Hooks | ☐ |
| 10-11 | | ☐ |
| 12-15 | Capstone | ☐ |
