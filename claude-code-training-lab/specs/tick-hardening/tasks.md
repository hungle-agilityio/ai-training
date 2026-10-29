# Tasks: tick-hardening

## T1: The tick guards against fork pull requests, pulls main, and repairs itself

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9, AC10
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_hardening.py` (new)
- **Depends on:** #70, #68 (both change `ops/agent_tick.py`)
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`
