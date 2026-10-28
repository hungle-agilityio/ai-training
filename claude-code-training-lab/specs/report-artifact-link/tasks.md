# Tasks: report-artifact-link

## T1: Loop pull requests always carry the verify report link

- **ACs:** AC1 to AC11
- **Files likely touched:** `.claude/settings.json`, `.claude/hooks/before-github-command-check.py`, `.claude/hooks/tests/test_report_link_guard.py` (new), `.claude/skills/work-queue/SKILL.md`, `.claude/skills/draft-pull-request/SKILL.md`, `.claude/knowledge/KNOWN_PITFALLS.md`
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (it changes `.claude/`, which the loop may not edit)
