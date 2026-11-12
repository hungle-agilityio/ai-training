# Spec: security-check

## Summary

Before a release reaches end users, `ops/release.py` runs three automatic security checks on the commit it will release (deploy settings, dependency audit, secret scan) and refuses the release when one fails; the release thread then runs a Claude security review of the changes since the last release and shows it on the "Phát hành" card. The app's production settings get clickjacking protection, a redirect to HTTPS and HSTS. The sign-in page refuses a username for 15 minutes after 5 wrong passwords. The only visible change is the new message on the sign-in page.

## User story

As the owner, I want every release checked for security problems before it reaches end users, so that I do not publish a known weakness by accident.

As a user of ReviewRadar, I want my account protected against password guessing and my session protected on the live site, so that nobody else can sign in as me.

## Acceptance criteria

**Production settings (T1)**

- **AC1.** `reviewradar/settings.py`: `django.middleware.clickjacking.XFrameOptionsMiddleware` is added at the end of `MIDDLEWARE` (Django's default `X_FRAME_OPTIONS = "DENY"` is kept). Every response carries `X-Frame-Options: DENY`, with `DJANGO_DEBUG` 1 or 0.
- **AC2.** When `DJANGO_DEBUG=0`: `SECURE_SSL_REDIRECT = True`, `SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]` (Render's health check calls `/healthz/` over plain HTTP inside its network), `SECURE_HSTS_SECONDS = 31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS = False`, `SECURE_HSTS_PRELOAD = False`. When `DJANGO_DEBUG=1` (local and tests): `SECURE_SSL_REDIRECT = False` and `SECURE_HSTS_SECONDS = 0`, so `runserver` keeps working over `http://`.
- **AC3.** With `DJANGO_DEBUG=0`, a real `DJANGO_SECRET_KEY` (50 random characters) and `DJANGO_ALLOWED_HOSTS=reviewradar.onrender.com`, `uv run python manage.py check --deploy --fail-level WARNING` exits 0 and prints `System check identified no issues (0 silenced).`
- **AC4.** With `DJANGO_DEBUG=0`: a request `GET /dashboard/` without `X-Forwarded-Proto: https` answers 301 to `https://<host>/dashboard/`; `GET /healthz/` without it answers 200 `ok`; a request with `X-Forwarded-Proto: https` gets the header `Strict-Transport-Security: max-age=31536000` (no `includeSubDomains`, no `preload`). New tests in `reviews/tests/integration/test_security_settings.py`; every test on `main` passes unchanged.

**Sign-in limit (T2)**

- **AC5.** Given the account `demo` and no failed sign-in in the last 15 minutes, when someone submits `/login/` with username `demo` and a wrong password 4 times, then each time the page shows Django's message `Please enter a correct username and password. Note that both fields may be case-sensitive.` as today, and the 5th wrong password shows the same message too.
- **AC6.** Given 5 wrong passwords for `demo` within 15 minutes, when someone submits `/login/` with username `demo` and the right password within 15 minutes of the 5th failure, then the sign-in is refused, nobody is signed in, and the page shows in the red error box exactly: `Too many failed sign-in attempts. Try again in 15 minutes.` The username field keeps `demo`, the password field is empty.
- **AC7.** Given that lock on `demo`, when 15 minutes have passed since the 5th failure and someone signs in with the right password, then the sign-in succeeds and goes to the dashboard as today, and the count for `demo` starts again at 0.
- **AC8.** The count is per username, compared after `strip()` and `casefold()` (`Demo `, `DEMO` and `demo` share one count), and counts usernames that have no account the same way, so the lock message never tells whether an account exists. Attempts made while a username is locked are refused without checking the password, are not counted and do not extend the lock. A successful sign-in sets the count of that username to 0. The window is 15 minutes from the first counted failure; the lock lasts 15 minutes from the 5th failure.
- **AC9.** The rule lives in a new service module `reviews/login_limit.py` (constants `MAX_FAILURES = 5`, `WINDOW_SECONDS = 900`, `LOCK_SECONDS = 900`, `LOCKED_MESSAGE` at the top) that keeps the counts in Django's default cache (no model, no migration, no new dependency; the counts reset when the app restarts). `reviews/forms.py` gets `LimitedAuthenticationForm`, a subclass of `django.contrib.auth.forms.AuthenticationForm` whose `clean()` asks the service before authenticating and records the result; `reviewradar/urls.py` passes it to `LoginView` as `authentication_form`. A `POST /login/` makes the same number of database queries as on `main` (1 with a wrong password, 9 with the right one). New tests in `reviews/tests/unit/test_login_limit.py` and `reviews/tests/integration/test_login_limit_page.py`, with time moved by `mocker` on the service's clock, never by sleeping; every test on `main` passes unchanged.

**Security checks in the release (T3)**

- **AC10.** A new script `ops/security_check.py` with `run_checks(sha: str, since: str | None, cwd: Path) -> tuple[CheckResult, ...]` (`CheckResult` a frozen dataclass: `name`, `ok`, `lines`) runs three checks, in this order, on the commit `sha` checked out in a temporary detached worktree (`git worktree add --detach`), which it removes afterwards, also after a failure:
  1. `deploy settings`: from the app folder of the worktree, `uv run --frozen python manage.py check --deploy --fail-level WARNING` with `DJANGO_DEBUG=0`, a new random `DJANGO_SECRET_KEY` of 50 characters (`secrets.token_urlsafe`) and `DJANGO_ALLOWED_HOSTS=reviewradar.onrender.com`. Ok when it exits 0; otherwise `lines` holds each line of its output that starts with `?:` or a path and contains `(security.`.
  2. `dependencies`: `uv export --frozen --no-dev --no-hashes --no-emit-project` into a temporary file, then `uvx pip-audit==2.10.1 -r <file> --no-deps --disable-pip --progress-spinner off --format json`. Ok when it exits 0; on exit 1 `lines` holds one line per vulnerability in its JSON (`dependencies[].vulns[]`), `<name> <version> <vulnerability id>`.
  3. `secrets`: the lines added in `git diff <since>..<sha>` (every tracked file of `sha` when `since` is None), matched against the pattern `SECRET` of `../plugins/agent-flow/hooks/before-commit-check.py` copied into the module as the constant `SECRET_PATTERN` (GitHub tokens, private key headers, AWS keys, Slack tokens, `sk-` keys), plus `sk-ant-[A-Za-z0-9_-]{20,}` for Anthropic keys, which that pattern misses. Ok when nothing matches; otherwise `lines` holds `<path>:<line number>`, never the matched text.
- **AC11.** A check whose tool cannot run (a command not found, no network, a timeout of 300 seconds, an exit code pip-audit does not document) is not ok, with the single line `could not run: <reason>`.
- **AC12.** `ops/release.py`: after the Checks and ancestor checks of `make_plan`, it calls `security_check.run_checks(sha, deploy or None, cwd)`. The plan gets the field `security: tuple[str, ...]` and `describe()` adds, after the pull request list, `Security checks:` and one line per check, `  deploy settings: ok` or `  deploy settings: FAILED` followed by its `lines` indented by four spaces, then `Security review diff: <deploy short sha>..<sha short sha>` (or `Security review diff: <sha short sha> (first release)`). When any check is not ok, the release is refused with exit 1: the security lines go to stderr, then the one line `security check failed: <names of the failed checks, comma separated>`; `--dry-run` refuses the same way, and nothing is tagged or pushed.
- **AC13.** New tests in `ops/tests/test_security_check.py` and `ops/tests/test_release_security.py`, with `subprocess.run` mocked (never the network, never a real `uvx`), cover: all ok, each check failing, a tool that cannot run, a secret line reported without its text, the worktree removed after a failure, and the dry-run and refusal output of AC12. Every test on `main` passes unchanged, except the tests a pinned-test run lists in the issue.

**Project rules (T4, built by hand)**

- **AC14.** `.claude/knowledge/decisions/ADR-031-security-check-before-release.md` records the decision (context: the owner's request of 2026-11-12 and the findings in `intent.md`; decision: AC1 to AC13 and AC15; rejected options of Q1 to Q5 below; the live check belongs to ADR-032). `.claude/knowledge/decisions/README.md` lists it.
- **AC15.** `.claude/project-instructions.md`, the Release paragraph: after the dry-run succeeds, the thread runs a security review of `git diff <Security review diff>` on the Mac mini with Claude Code's `/security-review` method (only findings of high or medium severity with high confidence), and the release card shows the dry-run output and the line `Security review: no findings.` or one line per finding (`<severity> <file>:<line> <one-line reason>`). With no finding the card is A "Phát hành (đề xuất)", B "Huỷ"; with a finding it is A "Huỷ (đề xuất)", B "Phát hành vẫn" and the owner decides. A dry-run refused by a security check shows its lines and the card offers only "Huỷ". `.claude/rules/security.md` gets a section "Before a release" that names the three checks of AC10 and the review of AC15. After the merge the owner pastes the Release paragraph into Project settings (the thread gives the exact text).

## Edge cases

- Empty: the first release (no `deploy` yet) scans every tracked file for secrets and reviews the whole tree; a release with no change in dependencies still runs the audit (a new vulnerability can be published for an old version); a review with no finding shows `Security review: no findings.`
- Large data: the checks run once per release, on one commit; the secret scan reads only added lines of the release diff; the sign-in counts are one small cache entry per username tried in the last 15 minutes.
- Permissions: only the release thread on the Mac mini runs `release.py`; the lock applies to every account the same way, including the owner's; anyone can lock a username for 15 minutes by guessing (accepted: the lock ends by itself, and the owner can restart the app to clear it).
- Error: a check that cannot run blocks the release (AC11); the app restarting clears all locks (AC9).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 What blocks a release? | The three automatic checks block; the Claude review is shown on the card and the owner decides | Everything blocks; nothing blocks (report only) | Automatic checks give a sure answer; an AI review can be wrong, so a person decides |
| Q2 Where does the Claude security review run? | Once per release, on the diff since the last release, by the release thread | In every loop build; not at all | One run per release, right before end users see it, and no clash with the work-queue files other work changes |
| Q3 How are the three deploy warnings fixed? | All three now: X-Frame-Options DENY, HTTPS redirect (`/healthz/` exempt), HSTS one year without subdomains or preload | HSTS for one hour first; only allow the warnings | Render serves only HTTPS, so one year is safe; without subdomains and preload it can still be undone |
| Q4 How is password guessing stopped? | Own code: 5 failures in 15 minutes per username lock it for 15 minutes, a general message, no new library | `django-axes`; later | Sign-in is open on the internet; a cache counter needs no migration and no dependency |
| Q5 Is the live site checked after a deploy? | Yes, after every release | No | Some settings only show on the live site behind Render's proxy; the "post-release checks" epic owns `ops/live_check.py` and takes the checks of AC2 to AC4 as its ACs |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

The sign-in page's lock message: [design/security-check/README.md](../../design/security-check/README.md). Nothing else is visible to users.

## Open questions
