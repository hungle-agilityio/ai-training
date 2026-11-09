# Tasks: loop-verify-failures

## T1: The hook names the plain command; verify inputs in out/verify-input/

- **ACs:** AC1, AC2, AC3, AC4
- **Files likely touched:** `../plugins/agent-flow/hooks/before-skill-script-allow.py`, `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/skills/build-verify-report/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/hooks/tests/test_skill_script_guidance.py` (NEW), `../plugins/agent-flow/tests/test_verify_input_paths.py` (NEW)
- **Existing tests that change:** `../plugins/agent-flow/tests/test_work_queue_criteria_format.py::test_plugin_version_is_raised_for_the_criteria_format` (expects `1.0.9`)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (the plugin's own guard hook and skills; outside the loop allow list)

## T2: Allow the four commands the builds needed

- **ACs:** AC5
- **Files likely touched:** `.claude/settings.json`, `ops/tests/test_loop_allow_rules.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)

## T3: List the existing tests an issue's ACs would change

- **ACs:** AC6, AC7, AC8, AC9
- **Files likely touched:** `ops/pinned_tests.py` (NEW), `ops/README.md`, `ops/tests/test_pinned_tests.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

T1, T2 and T3 share no file and can run in parallel. After T3 is merged, the Definition of Ready in the Project settings gets the line: "existing tests the ACs change are listed under `## Existing tests that change` (run `ops/pinned_tests.py`)".
