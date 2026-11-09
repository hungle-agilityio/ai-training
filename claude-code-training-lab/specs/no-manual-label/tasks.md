# Tasks: no-manual-label

All three tasks change the flow's own guards, which the loop cannot build before this change exists (Q5). They are built by hand, in order, in an interactive session on the Mac mini, and the owner clicks Merge on GitHub. They are the last tasks built this way.

## T1: The hook allows the files an issue lists; every issue is agent:ready

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC14
- **Files likely touched:** `../plugins/agent-flow/hooks/before-edit-check.py`, `../plugins/agent-flow/hooks/tests/test_before_edit_allowed_edits.py` (NEW), `../plugins/agent-flow/skills/create-issue/route_issue.py`, `../plugins/agent-flow/skills/create-issue/SKILL.md`, `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/skills/create-issue/tests/test_route_all_ready.py` (NEW)
- **Existing tests that change:**
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_issue.py::test_a_path_the_hook_refuses_makes_the_issue_manual`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_issue.py::test_a_path_without_an_allow_rule_needs_permission`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_issue.py::test_the_script_reads_the_allow_rules_from_the_settings_file`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_plugin_paths.py::test_a_plugin_path_is_flow_work_done_by_hand`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_plugin_paths.py::test_one_plugin_path_among_app_paths_decides`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_plugin_paths.py::test_only_app_paths_still_need_permission_when_not_allowed`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_test_edits.py::test_without_the_section_the_existing_test_is_manual`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_test_edits.py::test_listing_another_test_does_not_open_this_one`
  - `../plugins/agent-flow/skills/create-issue/tests/test_route_issue_flow_config.py::test_cli_with_dot_app_dir_keeps_paths_from_the_root`
- **Depends on:** none
- **Risk:** high
- **needs-ui:** no
- **Label:** built by hand on the Mac mini (owner clicks Merge)

## T2: The tick passes the list, stops skipping agent:manual and shows guard files

- **ACs:** AC6, AC7, AC8, AC9, AC10, AC13, AC14
- **Files likely touched:** `ops/agent_tick.py`, `ops/epic_pull_request.py`, `ops/bootstrap.py`, `ops/bootstrap_manifest.toml`, `ops/README.md`, `ops/tests/test_tick_allowed_edits.py` (NEW)
- **Existing tests that change:**
  - `ops/tests/test_tick_stacked.py::test_manual_child_does_not_start_stacked`
  - `ops/tests/test_tick_no_cap.py::test_ready_issue_held_by_a_skip_label_does_not_block_queue_empty`
  - `ops/tests/test_tick_waiting.py::test_skipped_issue_is_not_in_the_message`
  - `ops/tests/test_tick_guards.py::test_issue_waits_while_any_dependency_is_open`
  - `ops/tests/test_tick_retry_failed.py::test_manual_issue_is_never_retried`
  - `ops/tests/test_bootstrap_gaps.py::test_a_step_asks_for_edit_rules_without_the_flag`
- **Depends on:** T1 (the tick's variable is useless before the hook reads it)
- **Risk:** high
- **needs-ui:** no
- **Label:** built by hand on the Mac mini (owner clicks Merge)

## T3: ADR-023 and the rules

- **ACs:** AC11, AC12 (and the AC13 result in ADR-023)
- **Files likely touched:** `.claude/knowledge/decisions/ADR-023-no-manual-label.md` (NEW), `.claude/knowledge/decisions/ADR-012-spec-pull-request-and-scripted-loop.md`, `.claude/knowledge/decisions/ADR-019-flow-config-and-bootstrap.md`, `.claude/knowledge/decisions/ADR-020-flow-as-a-plugin.md`, `.claude/project-instructions.md`, `.claude/CLAUDE.md`, `docs/app/templates/spec/tasks.md`
- **Depends on:** T2
- **Risk:** medium
- **needs-ui:** no
- **Label:** built by hand on the Mac mini with T2 (owner clicks Merge)
