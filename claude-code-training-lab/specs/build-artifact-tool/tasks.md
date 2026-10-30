# Tasks: build-artifact-tool

## T1: A loop build that starts without the Artifact tool is started again

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_build_artifact_tool.py` (new), `ops/tests/test_agent_tick.py` (only the two tests named in AC8)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`
