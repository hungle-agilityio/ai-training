# Tasks: release-deploy

## T0: Change PR #101 (issue #65) to follow `deploy`

Not a new issue: a plain comment on pull request #101 and an edit of the "Done when" of issue #65.

- **ACs:** AC1, AC2, AC3
- **Files likely touched:** `render.yaml`, `claude-code-training-lab/README.md`, `claude-code-training-lab/reviews/tests/integration/test_render_blueprint.py` (the pull request's own new file)
- **Depends on:** this spec merged
- **Risk:** low
- **needs-ui:** no

## T1: Release script `ops/release.py`

- **ACs:** AC4, AC5, AC6, AC7, AC8, AC9, AC10, AC11
- **Files likely touched:** `claude-code-training-lab/ops/release.py` (new), `claude-code-training-lab/ops/tests/test_release.py` (new), `claude-code-training-lab/ops/README.md`
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: ADR-017, the "phát hành" command and the removal row

- **ACs:** AC12, AC13, AC14
- **Files likely touched:** `claude-code-training-lab/.claude/knowledge/decisions/ADR-017-deploy-by-release-branch.md` (new), `claude-code-training-lab/.claude/project-instructions.md`, `claude-code-training-lab/.claude/CLAUDE.md`
- **Depends on:** T1 (the command runs the script)
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual`, `area:flow` (changes `.claude/`)

AC15 and AC16 are checked by the owner after the first release and the Blueprint.
