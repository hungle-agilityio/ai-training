# Test matrix: guard-list-one-source

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | `guarded_kind` gives `rule`, `plugin`, `gate` or `None` for one path of each kind, in the order of AC1; the four sets hold exactly the names of AC1. | unit | `../plugins/agent-flow/hooks/tests/test_guarded_paths.py` | T1 |
| M2 | AC2 | normal | `before-edit-check.py` defines none of the four names or `guarded_kind` and imports them from `guarded_paths`; its refusal messages are those of `main`. | unit | `../plugins/agent-flow/hooks/tests/test_guarded_paths.py` | T1 |
| M3 | AC5 | normal | Loop mode, `ops/flow.toml` not listed: refused with the message of AC5; listed in `FLOW_ALLOWED_EDITS`: allowed; same for `.flow/flow.toml`. | integration | `../plugins/agent-flow/hooks/tests/test_guarded_paths.py` | T1 |
| M4 | AC3 | normal | `ops/epic_pull_request.py` has no `GUARD_DIRS`, `GUARD_NAMES`, `PLUGIN_ROOTS` or `GATE_FILES`; `guarded` follows `guarded_kind` and keeps the test-folder rule. | unit | `ops/tests/test_guard_list_one_source.py` | T1 |
| M5 | AC4 | error | `paths.plugin_dir` pointing at a folder without the module: `guarded` is True for `reviews/services.py`; no exception. | unit | `ops/tests/test_guard_list_one_source.py` | T1 |
| M6 | AC6 | normal | `guard_paths` of a name-status with `M claude-code-training-lab/ops/flow.toml` lists it. | unit | `ops/tests/test_guard_list_one_source.py` | T1 |
| M7 | AC6 | empty | `guard_paths` of a name-status with only `M reviews/services.py` is empty. | unit | `ops/tests/test_guard_list_one_source.py` | T1 |
| M8 | AC7, AC8 | normal | Parity over the fixed list of AC7; `plugin.json` version above `main` (`check_plugin_version.py` passes in CI). | integration | `ops/tests/test_guard_list_one_source.py` | T1 |
| M9 | AC10 | normal | ADR-023 has the new consequence line and not the old one. | manual | Read the ADR on `main` after the merge. | T2 |
