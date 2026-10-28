# Tasks: <feature>

<!-- Copy to specs/<feature>/tasks.md. One task becomes one issue. Tasks meant to run in parallel never share a file. Keep each task under about 400 lines of diff. -->

## T1: <short title>

- **ACs:** AC1, AC2
- **Files likely touched:** `reviews/services.py`, `reviews/tests/unit/test_<name>.py`
- **Depends on:** none
- **Risk:** low | medium | high
- **needs-ui:** yes | no
- **Label:** `agent:ready`, or `agent:manual` when it changes `.claude/`

## T2: <short title>

- **ACs:** AC3
- **Files likely touched:** <paths>
- **Depends on:** T1
- **Risk:** low | medium | high
- **needs-ui:** yes | no
- **Label:** `agent:ready`
