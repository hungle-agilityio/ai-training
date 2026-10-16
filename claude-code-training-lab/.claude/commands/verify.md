---
description: Final verification, PASS / FAIL / NOT CONFIGURED per axis
argument-hint: <issue number or folder>
---

Verify the work for: $ARGUMENTS

Give one line per axis, `PASS`, `FAIL` or `NOT CONFIGURED`, with the evidence:

| Axis | How |
|---|---|
| Lint | `uv run ruff check .` |
| Types | `uv run mypy .` |
| Tests | `uv run pytest -q --no-cov` |
| Coverage | `uv run pytest`; 90% on services and repositories |
| Issue | each "Done when" or acceptance criterion of the issue, checked in the running app or a test |
| Query count | asserted for list and dashboard pages |
| Security | `.claude/rules/security.md`, no secrets in the diff |

If an axis cannot be checked, write `NOT CONFIGURED` and why; never write PASS without evidence.

**Then stop at Gate 2.** Ask me to check the result myself (steps to try in the app when the issue is visible). Do not commit or run `/learn` until I say OK.
