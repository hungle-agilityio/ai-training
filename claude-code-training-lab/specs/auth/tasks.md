# Tasks: auth

One epic issue, "Epic: sign in to ReviewRadar", holds the five tasks below as GitHub sub-issues and a checklist. The epic has no `agent:` label, so the loop never picks it, and no task says `Depends on` the epic (the epic stays open until the release, so such a task would wait for ever). The owner closes the epic after the release (AC26).

Order: T1 and T2 start at once. T3 waits for both. T4 waits for T2; T5 waits for T1. T3 is `risk:high`, so it runs alone; T4 and T5 share no file and run side by side.

## T1: Test set-up for sign-in and the `/healthz/` health path

- **ACs:** AC1, AC2, AC3
- **Files likely touched:** `reviews/tests/conftest.py` (NEW), `render.yaml` (repository root), `reviews/tests/integration/test_render_blueprint.py`
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual`, `area:app` (`conftest.py` and an existing test are protected from the loop; done in an interactive session on the Mac mini after the owner's OK)

## T2: Sign-in and sign-out pages

- **ACs:** AC4, AC5, AC6, AC7, AC8, AC9, AC10
- **Files likely touched:** `reviewradar/settings.py`, `reviewradar/urls.py`, `reviews/views.py`, `reviews/templates/registration/login.html` (NEW), `reviews/static/reviews/app.css`, `reviews/tests/integration/test_sign_in.py` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

## T3: Every page needs an account

- **ACs:** AC11, AC12, AC13, AC14, AC15, AC16
- **Files likely touched:** `reviewradar/settings.py`, `reviews/tests/integration/test_login_required.py` (NEW)
- **Depends on:** T1 (the `login` marker), T2 (the sign-in page and the middleware before it)
- **Risk:** high
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

## T4: "Signed in as" and "Sign out" in the sidebar

- **ACs:** AC17, AC18, AC19, AC20
- **Files likely touched:** `reviews/templates/reviews/base.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_sidebar_account.py` (NEW)
- **Depends on:** T2 (the `/logout/` URL and `app.css`)
- **Risk:** low
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

## T5: `create_user` command and the demo user

- **ACs:** AC21, AC22, AC23, AC24, AC25
- **Files likely touched:** `reviews/management/commands/create_user.py` (NEW), `reviews/management/commands/seed_demo_data.py`, `render.yaml` (repository root), `README.md`, `reviews/tests/integration/test_accounts.py` (NEW)
- **Depends on:** T1 (both change `render.yaml`)
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

AC26 is checked by the owner after the release of the whole epic.
