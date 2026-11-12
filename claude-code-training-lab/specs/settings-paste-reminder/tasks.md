# Tasks: settings-paste-reminder

Two tasks, not an epic. T1 changes `ops/release.py` after the GitHub Release page task of `specs/release-page/` (same file). T2 changes `.claude/project-instructions.md`, so it is built by hand (ADR-023, "Exception: .claude/"), one after the other with the other hand tasks on the same Release paragraph.

## T1: Reminder line in the release plan

- **ACs:** AC1 to AC5
- **Matrix rows:** M1 to M6
- **Files likely touched:** `ops/release.py`, `ops/README.md`, `ops/tests/test_release_settings_reminder.py` (NEW), `specs/settings-paste-reminder/decisions/T1.md` (NEW)
- **Depends on:** the T1 task of `specs/release-page/` (same file)
- **Risk:** medium (the release script)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: The release thread gives the text to paste

- **ACs:** AC6
- **Matrix rows:** M7
- **Files likely touched:** `.claude/project-instructions.md`
- **Depends on:** T1, and the hand tasks that change the same Release paragraph
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand), `area:flow`
