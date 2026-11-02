# Tasks: loop-depends

## T1: The tick tidies merged pull requests itself and says which ready issues wait, and why

- **ACs:** AC1 to AC9
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_waiting.py` (new), `ops/tests/test_agent_tick.py` (only the two cases named below)
- **Existing tests:** in `ops/tests/test_agent_tick.py`, `test_pull_request_that_needs_a_run_is_taken`, the cases `merged-with-label` and `closed-issue-in-review` now expect no build; move them into the new file as AC1 tests and delete them from the parametrize list. No other existing test changes.
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`
