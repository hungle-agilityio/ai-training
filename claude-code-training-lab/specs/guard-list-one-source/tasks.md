# Tasks: guard-list-one-source

Two tasks, not an epic. T2 changes a file under `.claude/`, so it is built by hand after T1 (ADR-023, "Exception: .claude/").

## T1: One guarded-files rule in the plugin

- **ACs:** AC1 to AC9
- **Matrix rows:** M1 to M8
- **Files likely touched:** `../plugins/agent-flow/hooks/guarded_paths.py` (NEW), `../plugins/agent-flow/hooks/before-edit-check.py`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/hooks/tests/test_guarded_paths.py` (NEW), `ops/epic_pull_request.py`, `ops/tests/test_guard_list_one_source.py` (NEW), `specs/guard-list-one-source/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** medium (the loop's guards)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: ADR-023 names the one source

- **ACs:** AC10
- **Matrix rows:** M9
- **Files likely touched:** `.claude/knowledge/decisions/ADR-023-no-manual-label.md`
- **Depends on:** T1
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand), `area:flow`
