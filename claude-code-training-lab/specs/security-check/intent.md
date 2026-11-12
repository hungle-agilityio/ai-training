# Intent: security-check

## Problem

A release moves `deploy`, and Render puts the app in front of end users, after only one gate: green Checks on `main` (`ops/release.py`). Checks test behaviour, not security. On 2026-11-12 (`main` fb05984) the owner asked for a step that judges security and the other risks to the app before a release reaches end users. What we found that day:

- `python manage.py check --deploy` with the production settings gives three warnings: no `X-Frame-Options` header (the pages can be framed: clickjacking), no HSTS, and no redirect from `http://` to `https://`.
- Nothing audits the locked dependencies before a release (Dependabot opens pull requests weekly but blocks nothing). The audit that day (`pip-audit`, Django 5.2.18, gunicorn 26.2.0) found no known vulnerability.
- Nothing scans what is released for keys or tokens; only the commit hook on the Mac mini does, and only for commits made there.
- No security-minded review of the changes being released: the `/code-review` of each build (spec `test-harden`) looks for bugs, not for attacks.
- The sign-in page accepts any number of wrong passwords, so a password can be guessed by trying.

## Goal

1. `ops/release.py` refuses a release when the deploy settings check, the dependency audit or the secret scan fails, and its dry-run shows the result of each.
2. The release thread runs a Claude security review of the changes since the last release and shows its findings on the "Phát hành" card; the owner decides.
3. The three deploy warnings are fixed in the settings.
4. After 5 wrong passwords in 15 minutes for one username, sign-in for that username is refused for 15 minutes.

## Users

End users of ReviewRadar (staff of the businesses), who sign in on the live site; the owner, who releases; the release thread on the Mac mini.

## Out of scope

- Checking the live site after a deploy (HTTPS, headers, pages need sign-in): the epic "post-release checks, rollback and monitoring" owns `ops/live_check.py` and takes those checks as its ACs.
- A `/security-review` in every loop build; ultrareview in the flow.
- Content-Security-Policy, two-factor sign-in, a web application firewall, GitHub Advanced Security.
- Limiting sign-in by IP address (behind Render's proxy the address can be forged).
- Changing releases that already exist.
