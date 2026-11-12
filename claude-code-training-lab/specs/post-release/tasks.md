# Tasks: post-release

One epic, in order of priority: the live check and the rollback first. T1 and T5 change the app and run side by side with T2. T2 → T3 → T4 run one after the other because each adds a section to `ops/README.md` (T3 also reuses the `[live]` config of T2). T6 waits for test-harden T4 (`ops/regression_screens.json`, the browser steps in `checks.yml`, the bootstrap patterns). T2 waits for test-harden T1 (`ops/flow_config.py`, `ops/flow.toml`) and T4, and for security-check T1 (the headers its AC8 checks). T5 waits for security-check T1 (same file `reviewradar/settings.py`). T1 to T6 are `agent:ready` and merge into the epic branch; the owner reviews the one epic pull request. T7 changes files under `.claude/` and is built by hand on `main` after the epic merges and after the security-check ADR-031 task (ADR-023, "Exception: .claude/"); the owner clicks Merge.

## Query budget

| Page | Queries on main | After T1 | After T6 |
|---|---|---|---|
| `/healthz/` | 0 | 0 | 0 |

No other page changes its queries (T6 changes only `app.css`). No task of the epic adds a query-cap test other than the zero-query test of `/healthz/` in T1.

## T1: Release commit on /healthz/

- **ACs:** AC1, AC2
- **Matrix rows:** M1 to M3
- **Files likely touched:** `reviews/views.py`, `reviews/tests/integration/test_healthz_commit.py` (NEW), `specs/post-release/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no (a response header only)
- **Label:** `agent:ready`, `area:app`

## T2: Live check after a release

- **ACs:** AC3, AC4, AC5, AC6, AC7, AC8, AC9, AC10
- **Matrix rows:** M4 to M15
- **Files likely touched:** `ops/live_check.py` (NEW), `ops/flow_config.py`, `ops/flow.toml`, `ops/agent.env.example`, `ops/README.md`, `ops/tests/test_live_check.py` (NEW), `specs/post-release/decisions/T2.md` (NEW)
- **Depends on:** T1; test-harden T1 and T4; security-check T1
- **Risk:** medium (the release hand-over)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T3: Rollback through Render's API

- **ACs:** AC11, AC12, AC13, AC14, AC15
- **Matrix rows:** M16 to M23
- **Files likely touched:** `ops/rollback.py` (NEW), `ops/README.md`, `ops/tests/test_rollback.py` (NEW), `specs/post-release/decisions/T3.md` (NEW)
- **Depends on:** T2
- **Risk:** medium (acts on the live site)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T4: Uptime alert from the loop

- **ACs:** AC16, AC17, AC18
- **Matrix rows:** M24 to M29
- **Files likely touched:** `ops/uptime.py` (NEW), `ops/start-loop.sh`, `ops/README.md`, `ops/tests/test_uptime.py` (NEW), `specs/post-release/decisions/T4.md` (NEW)
- **Depends on:** T3
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T5: Server errors to Sentry

- **ACs:** AC19, AC20, AC21
- **Matrix rows:** M30 to M33
- **Files likely touched:** `pyproject.toml`, `uv.lock`, `reviewradar/monitoring.py` (NEW), `reviewradar/settings.py`, `../render.yaml`, `reviews/tests/unit/test_error_tracking.py` (NEW), `reviews/tests/integration/test_render_sentry_env.py` (NEW), `specs/post-release/decisions/T5.md` (NEW)
- **Depends on:** security-check T1
- **Risk:** medium (new runtime dependency, settings)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T6: Accessibility of the main screens in CI

- **ACs:** AC22, AC23, AC24, AC25
- **Matrix rows:** M34 to M41
- **Files likely touched:** `reviews/static/reviews/app.css`, `ops/a11y_check.py` (NEW), `ops/vendor/axe.min.js` (NEW), `../.github/workflows/checks.yml`, `ops/bootstrap.py`, `ops/bootstrap_manifest.toml`, `ops/bootstrap_layout.py`, `ops/tests/test_a11y_check.py` (NEW), `specs/post-release/decisions/T6.md` (NEW)
- **Depends on:** test-harden T4
- **Risk:** low
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` → `.badge-positive` (first goal badge); `/reviews/` → `.followup-resolved`; `/settings/` → `#settings-suggestions`
- **Label:** `agent:ready`, `area:app`

## T7: ADR-032 and the Project commands

- **ACs:** AC26, AC27
- **Matrix rows:** M42, M43
- **Files likely touched:** `.claude/knowledge/decisions/ADR-032-post-release-checks.md` (NEW), `.claude/knowledge/decisions/ADR-017-deploy-by-release-branch.md`, `.claude/knowledge/decisions/README.md`, `.claude/CLAUDE.md`, `.claude/project-instructions.md`
- **Depends on:** T1 to T6 (after the epic merges); the security-check ADR-031 task (same files)
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception), `area:flow`
