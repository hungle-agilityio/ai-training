# Test matrix: starter-refresh

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | `bootstrap.py --stack python` into an empty clone writes 26 files `docs/decisions/ADR-008-*.md` to `ADR-033-*.md`. | integration | `ops/tests/test_bootstrap_starter_refresh.py` | T1 |
| M2 | AC2 | normal | Every `ADR-NNN` cited in `.md` files under `.claude/` and `.flow/plugin/` of the output has its file in `docs/decisions/`. | integration | `ops/tests/test_bootstrap_starter_refresh.py` | T1 |
| M3 | AC3 | normal | The `## Index` of the output's `docs/decisions/README.md` links exactly its `ADR-*.md` files; the old layout's index is unchanged. | integration | `ops/tests/test_bootstrap_starter_refresh.py` | T1 |
| M4 | AC4 | normal | No copied text of the `--stack` output contains `design/app/`; the Project instructions contain `docs/design/prototype.html`. | integration | `ops/tests/test_bootstrap_starter_refresh.py` | T1 |
| M5 | AC5 | normal | The output's `.flow/flow.toml` `[paths]` has `spec_pr_dirs` with `docs/design` and `flow_dirs` with `docs/design/`. | unit | `ops/tests/test_bootstrap_starter_refresh.py` | T1 |
| M6 | AC6, AC7 | normal | The output's Project instructions name `docs/intent/`, `docs/specs/` and `docs/design/` for the spec pull request; `docs/design/README.md` has the one line of AC7. | integration | `ops/tests/test_bootstrap_starter_refresh.py` | T1 |
| M7 | AC8 | normal | `uv run pytest -q` passes. | integration | (whole suite) | T1 |
| M8 | AC9, AC10 | normal | In the template pull request: the kept files are unchanged, `docs/decisions/` has ADR-008 to ADR-033, the template tests pass. | manual | Steps: check the diff and paste the test output in the pull request | T2 |
| M9 | AC11 | normal | The kickoff instructions and the Notion page have the Prototype step. | manual | Steps: read both texts | T2 |
| M10 | AC12 | normal | "Nguồn của flow" names ADR-008 to ADR-033 and the date. | manual | Steps: read the page | T2 |
