# Test matrix: security-check

Written from the ACs of `spec.md` before any build. Only the sign-in lock (AC5 to AC8) is seen by users; the other ACs are technical and keep the plain form.

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | `GET /login/` answers with `X-Frame-Options: DENY`, with `DEBUG` True and False | integration | `reviews/tests/integration/test_security_settings.py` | T1 |
| M2 | AC2 | normal | Settings loaded in a subprocess with `DJANGO_DEBUG=0` and a real key have `SECURE_SSL_REDIRECT is True`, `SECURE_REDIRECT_EXEMPT == [r"^healthz/$"]`, `SECURE_HSTS_SECONDS == 31536000`, subdomains and preload False | unit | same | T1 |
| M3 | AC2 | edge | Settings loaded with `DJANGO_DEBUG=1` have `SECURE_SSL_REDIRECT is False` and `SECURE_HSTS_SECONDS == 0` | unit | same | T1 |
| M4 | AC3 | normal | `manage.py check --deploy --fail-level WARNING` in a subprocess with the production env of AC3 exits 0 and prints `System check identified no issues (0 silenced).` | integration | same | T1 |
| M5 | AC4 | normal | With the AC2 settings (`override_settings`): `GET /dashboard/` over http answers 301 to `https://testserver/dashboard/`; `GET /healthz/` over http answers 200 `ok`; a request with `X-Forwarded-Proto: https` carries `Strict-Transport-Security: max-age=31536000` | integration | same | T1 |
| M6 | AC5 | normal | Given `demo` with no failure, when 4 then a 5th wrong password are posted, then each page shows `Please enter a correct username and password. Note that both fields may be case-sensitive.` | integration | `reviews/tests/integration/test_login_limit_page.py` | T2 |
| M7 | AC5 | empty | Given no failure for `demo`, when the right password is posted, then it signs in and redirects to `/dashboard/` as on `main` | integration | same | T2 |
| M8 | AC6 | normal | Given 5 wrong passwords for `demo`, when the right password is posted within 15 minutes, then status 200, no session user, the page shows `Too many failed sign-in attempts. Try again in 15 minutes.`, the username field holds `demo`, the password field is empty | integration | same | T2 |
| M8b | AC6 | empty | n/a: the lock needs 5 earlier failures; with none, AC5 and M7 apply | integration | same | T2 |
| M9 | AC7 | normal | Given the lock, when the clock is moved 15 minutes past the 5th failure and the right password is posted, then it redirects to `/dashboard/`, and one more wrong password shows the AC5 message (count restarted) | integration | same | T2 |
| M9b | AC7 | empty | n/a: with no lock, M7 already shows the normal sign-in | integration | same | T2 |
| M10 | AC8 | edge | `Demo `, `DEMO` and `demo` share one count; a username with no account locks after 5 failures with the same message; attempts while locked are not counted and do not extend the lock | unit | `reviews/tests/unit/test_login_limit.py` | T2 |
| M11 | AC8 | edge | 4 failures, then a success, then 4 failures: no lock; failures spread over more than 15 minutes from the first: no lock | unit | same | T2 |
| M12 | AC9 | normal | `reviews/login_limit.py` has `MAX_FAILURES == 5`, `WINDOW_SECONDS == 900`, `LOCK_SECONDS == 900`, `LOCKED_MESSAGE`; `LoginView` in `reviewradar/urls.py` uses `LimitedAuthenticationForm` | unit | same | T2 |
| M13 | AC9 | normal | `POST /login/` makes 1 query with a wrong password and 9 with the right one (`django_assert_num_queries`) | integration | `reviews/tests/integration/test_login_limit_page.py` | T2 |
| M14 | AC10 | normal | With `subprocess.run` mocked to succeed for each command, `run_checks` returns three ok results named `deploy settings`, `dependencies`, `secrets`, in that order, and the worktree add and remove commands run | unit | `ops/tests/test_security_check.py` | T3 |
| M15 | AC10 | error | `check --deploy` output with `?: (security.W004) ...` and exit 1 gives `deploy settings` not ok with that line | unit | same | T3 |
| M16 | AC10 | error | pip-audit exit 1 with JSON of one vulnerability gives `dependencies` not ok with `<name> <version> <id>` | unit | same | T3 |
| M17 | AC10 | error | A diff that adds `token = "ghp_` + 36 letters in `reviews/x.py` line 3 gives `secrets` not ok with `reviews/x.py:3`, and the token text is in no line; an added `sk-ant-` key is found too; `since=None` scans the tracked files | unit | same | T3 |
| M18 | AC11 | error | A `FileNotFoundError`, a `TimeoutExpired` and an exit code 2 from pip-audit each give `could not run: <reason>`; the worktree is removed after an exception | unit | same | T3 |
| M19 | AC12 | normal | A dry-run with all checks ok prints `Security checks:`, the three `ok` lines and `Security review diff: <deploy7>..<sha7>`, exit 0 | unit | `ops/tests/test_release_security.py` | T3 |
| M20 | AC12 | error | A failed `secrets` check makes both the dry-run and the real run exit 1, print the security lines and `security check failed: secrets` to stderr, and tag and push nothing | unit | same | T3 |
| M21 | AC12 | edge | The first release (no `deploy`) passes `since=None` and prints `Security review diff: <sha7> (first release)` | unit | same | T3 |
| M22 | AC14 | normal | ADR-031 exists with context, decision, rejected options; `decisions/README.md` lists it | manual | Read the diff | T4 |
| M23 | AC15 | normal | The Release paragraph of `project-instructions.md` names the security review, its card texts with and without findings, and the "Huỷ"-only card on a refused dry-run; `rules/security.md` has "Before a release" | manual | Read the diff; the next "phát hành" shows the lines | T4 |
