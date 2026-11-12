# Tasks: epic-review-checklist

Two tasks, not an epic. T2 changes `.claude/project-instructions.md`, so it is built by hand (ADR-023, "Exception: .claude/"), after the post-release task that changes the same Release paragraph (AC27 of `specs/post-release/spec.md`).

## T1: Review checklist in the epic pull request

- **ACs:** AC1 to AC4
- **Matrix rows:** M1 to M4
- **Files likely touched:** `ops/epic_pull_request.py`, `ops/tests/test_epic_review_checklist.py` (NEW), `specs/epic-review-checklist/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: Live AC check after a release

- **ACs:** AC5, AC6
- **Matrix rows:** M5, M6
- **Files likely touched:** `.claude/project-instructions.md`
- **Depends on:** the post-release task of AC27 (`.claude/project-instructions.md`), and `ops/live_check.py` on `main`
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand), `area:flow`
