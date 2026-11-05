# Tasks: verify-screenshots

T1 comes first. T2 depends on T1 because it reads `element_screenshot` from `result.json`. T3 depends on T2 because it uses `--no-ui`. All three tasks change `.claude/`, so they are `agent:manual` and get built in one interactive session on the Mac mini. All are `area:flow` and `needs-ui: no`, since app users see no change. New tests go in new test files. None of them shares a file with #194, #199 or #201, which change `ops/`.

## T1: Browser check captures a close-up of the changed element

- **ACs:** AC1 to AC4
- **Files likely touched:** `.claude/skills/check-in-browser/browser_check.py`, `.claude/skills/check-in-browser/SKILL.md`, `.claude/skills/check-in-browser/tests/test_capture_element.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)

## T2: Verify report shows only the named screens, none for non-UI tasks

- **ACs:** AC5 to AC10
- **Files likely touched:** `.claude/skills/build-verify-report/build_report.py`, `.claude/skills/build-verify-report/SKILL.md`, `.claude/skills/build-verify-report/tests/test_report_screens.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (every loop pull request goes through this report and its share gate)
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)

## T3: Loop and issues name the screens to capture

- **ACs:** AC11 to AC15
- **Files likely touched:** `.claude/skills/work-queue/SKILL.md`, `.claude/skills/write-issue/SKILL.md`, `.claude/commands/verify.md`, `docs/app/templates/task.md`, `docs/app/templates/feature.md`, `docs/app/templates/bug.md`, `docs/app/templates/spec/tasks.md`
- **Depends on:** T2
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)

## After all are merged (not an issue)

1. Before T3 is merged, a thread adds a `## Screens to capture` block to each open `needs-ui` + `agent:ready` issue (edge case in spec.md).
2. The project instructions (step "Issues") gain one line: "a `## Screens to capture` block when needs-ui". The owner pastes that line.
