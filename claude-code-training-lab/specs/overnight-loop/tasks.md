# Tasks: overnight-loop

T1 and T3 can run at once (no shared file). T2 and T4 change `ops/agent_tick.py` after T1, so they run one after the other. Issue #149 is rewritten as T1.

## T1: The tick retries a failed issue up to 3 times when a retry can help

- **ACs:** AC1 to AC6 (without the parent part of AC1 to AC3, added in T4)
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_retry_failed.py` (new)
- **Existing tests:** none change; if one must, stop and report it.
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready` (rewrite of #149)

## T2: The tick has no pull request limit

- **ACs:** AC7, AC8, and the pull request list limit 40 -> 100
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_no_cap.py` (new), `ops/tests/test_agent_tick_waiting_cap.py`, `ops/tests/test_agent_tick_waiting_cap_ten.py`, `ops/tests/test_tick_notify_cases.py`, `ops/tests/test_tick_waiting.py`
- **Existing tests:** the issue permits deleting `test_agent_tick_waiting_cap.py` and `test_agent_tick_waiting_cap_ten.py`, and removing only the cap cases from `test_tick_notify_cases.py` and `test_tick_waiting.py` (named in the issue). No other existing test changes.
- **Depends on:** T1
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T3: work-queue opens a stacked pull request into its parent's branch; ADR-018

- **ACs:** AC17, AC18 (ADR and the superseded lines; `ops/README.md` is in T4)
- **Files likely touched:** `.claude/skills/work-queue/SKILL.md`, `.claude/skills/create-pull-request/SKILL.md`, `.claude/knowledge/decisions/ADR-018-stacked-pull-requests-and-retries.md` (new), `.claude/knowledge/decisions/README.md`, `.claude/CLAUDE.md`
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)

## T4: The tick starts a task on its parent's green pull request

- **ACs:** AC9 to AC16, the parent part of AC1 to AC3, `ops/README.md` for AC9 to AC16
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_stacked.py` (new)
- **Existing tests:** none change; if one must, stop and report it.
- **Depends on:** T2, T3
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:ready`
