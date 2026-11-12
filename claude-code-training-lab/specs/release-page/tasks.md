# Tasks: release-page

Two tasks, not an epic. T2 changes `.claude/project-instructions.md`, so it is built by hand (ADR-023, "Exception: .claude/"), after T1 and after the post-release task that changes the same Release paragraph (AC27 of `specs/post-release/spec.md`).

## T1: GitHub Release page from the release script

- **ACs:** AC1 to AC5
- **Matrix rows:** M1 to M6
- **Files likely touched:** `ops/release.py`, `ops/README.md`, `ops/tests/test_release_github_page.py` (NEW), `specs/release-page/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** medium (the release script)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: The release thread passes the notes link

- **ACs:** AC6
- **Matrix rows:** M7
- **Files likely touched:** `.claude/project-instructions.md`
- **Depends on:** T1, the post-release task of AC27
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand), `area:flow`
