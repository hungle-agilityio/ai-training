# Tasks: security-check

One epic. T1, T2 and T3 run side by side (no shared file) and merge into the epic branch; the owner reviews the one epic pull request. T3 waits for test-harden T5, which also changes `ops/release.py`. T4 changes files under `.claude/` and is built by hand on `main` after the epic merges (ADR-023, "Exception: .claude/"), after test-harden T6 and the ADR-030 task of the prototype step, which change the same files; the owner clicks Merge.

The live check after a deploy is not a task here: the epic "post-release checks, rollback and monitoring" owns `ops/live_check.py` and its `reviewradar/settings.py` change; both depend on T1.

## Query budget

| Page | Queries on main | After T1 | After T2 | After T3 |
|---|---|---|---|---|
| `POST /login/`, wrong password | 1 | 1 | 1 | 1 |
| `POST /login/`, right password | 9 | 9 | 9 | 9 |
| `POST /login/`, username locked | n/a | n/a | 0 | 0 |

No earlier task of the epic adds a query-cap test; T2 adds the caps of AC9.

## T1: Production security settings

- **ACs:** AC1, AC2, AC3, AC4
- **Matrix rows:** M1 to M5
- **Files likely touched:** `reviewradar/settings.py`, `reviews/tests/integration/test_security_settings.py` (NEW), `specs/security-check/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no (headers and redirects only; no page changes)
- **Label:** `agent:ready`, `area:app`

## T2: Lock sign-in after 5 wrong passwords

- **ACs:** AC5, AC6, AC7, AC8, AC9
- **Matrix rows:** M6 to M13 (with M8b, M9b)
- **Files likely touched:** `reviews/login_limit.py` (NEW), `reviews/forms.py`, `reviewradar/urls.py`, `reviews/tests/unit/test_login_limit.py` (NEW), `reviews/tests/integration/test_login_limit_page.py` (NEW), `specs/security-check/decisions/T2.md` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** yes
- **Screens to capture:** `/login/` after 5 wrong passwords for `demo` then a 6th attempt → `.signin-card`
- **Label:** `agent:ready`, `area:app`

## T3: Security checks in the release script

- **ACs:** AC10, AC11, AC12, AC13
- **Matrix rows:** M14 to M21
- **Files likely touched:** `ops/security_check.py` (NEW), `ops/release.py`, `ops/tests/test_security_check.py` (NEW), `ops/tests/test_release_security.py` (NEW), `specs/security-check/decisions/T3.md` (NEW)
- **Depends on:** test-harden T5 (same file `ops/release.py`); T1 (until T1 merges, the deploy settings check refuses every release)
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T4: ADR-031 and the release rules

- **ACs:** AC14, AC15
- **Matrix rows:** M22, M23
- **Files likely touched:** `.claude/knowledge/decisions/ADR-031-security-check-before-release.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/project-instructions.md`, `.claude/rules/security.md`
- **Depends on:** T1, T2, T3 (after the epic merges); test-harden T6; the ADR-030 task of the prototype step
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception), `area:flow`
