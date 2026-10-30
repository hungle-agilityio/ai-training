# Spec: auth

## Summary

ReviewRadar gets a sign-in page and every page needs an account. A visitor who is not signed in is sent to `/login/` and comes back to the page they asked for after signing in. A signed-in user sees "Signed in as <username>" and a "Sign out" button at the bottom of the sidebar. Accounts are made with a new command, `manage.py create_user`; passwords are reset with Django's own `manage.py changepassword`. `seed_demo_data` makes a `demo` account when `REVIEWRADAR_DEMO_PASSWORD` is set, so the Render demo stays usable. Render checks the new public `/healthz/` path instead of `/dashboard/`. It uses Django's built-in `User`, sessions and `LoginRequiredMiddleware` (Django 5.2): no package, no change to the `reviews` models.

The work is one epic issue with five sub-task issues (`tasks.md`). The live site changes only at the release after the whole epic is merged (ADR-017).

## Acceptance criteria

Test set-up and health path (T1, done by hand):

- **AC1.** A new `reviews/tests/conftest.py` registers the pytest marker `login` and, for every test not marked `login`, removes `django.contrib.auth.middleware.LoginRequiredMiddleware` from `settings.MIDDLEWARE` (pytest-django `settings` fixture), so the tests already on main keep running without signing in and keep their query counts. A test marked `login` runs with the real middleware list.
- **AC2.** `render.yaml` has `healthCheckPath: /healthz/`, and `reviews/tests/integration/test_render_blueprint.py` expects `/healthz/`.
- **AC3.** `uv run pytest -q` passes with no other test changed.

Sign in and sign out (T2):

- **AC4.** `INSTALLED_APPS` adds `django.contrib.sessions`. `MIDDLEWARE` keeps SecurityMiddleware first and WhiteNoiseMiddleware second, then adds `SessionMiddleware`, `CsrfViewMiddleware` and `AuthenticationMiddleware` in that order. `AUTH_PASSWORD_VALIDATORS` holds Django's four default validators. `LOGIN_URL = "login"`, `LOGIN_REDIRECT_URL = "dashboard"`, `LOGOUT_REDIRECT_URL = "login"`. `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are `True` when `DJANGO_DEBUG=0` and `False` otherwise.
- **AC5.** `GET /login/` answers 200 with the page of the design card: no sidebar, the ReviewRadar mark and name, heading "Sign in", the line "Use the account your ReviewRadar admin gave you.", fields "Username" and "Password", the button "Sign in", and the line "Forgot your password? Ask your ReviewRadar admin to reset it." The template is `reviews/templates/registration/login.html` and uses `app.css`; the form has a CSRF token.
- **AC6.** A POST with a right username and password signs the user in and redirects (302) to the `next` page when it is a path on this site, otherwise to `/dashboard/`. A wrong pair answers 200 on the same page with Django's text "Please enter a correct username and password. Note that both fields may be case-sensitive.", keeps the username and clears the password. An empty field shows Django's "This field is required.".
- **AC7.** A signed-in user who opens `/login/` is redirected to `/dashboard/`.
- **AC8.** `POST /logout/` signs the user out and redirects to `/login/`. `GET /logout/` answers 405 (Django's default) and does not sign out.
- **AC9.** `GET /healthz/` answers 200 with the body `ok`, makes no database query, and is marked `login_not_required`.
- **AC10.** Tests in a new file `reviews/tests/integration/test_sign_in.py` cover AC4 to AC9.

Every page needs an account (T3):

- **AC11.** `django.contrib.auth.middleware.LoginRequiredMiddleware` comes right after `AuthenticationMiddleware`.
- **AC12.** A visitor who is not signed in gets a 302 to `/login/?next=<path>` for `/`, `/dashboard/`, `/reviews/` (with its query string kept in `next`), `/reviews/export/` and `/api/dashboard/`.
- **AC13.** Without signing in: `/login/` and `/healthz/` answer 200, static files are served, and an unknown path answers the 404 page.
- **AC14.** A signed-in user gets 200 on every page of AC12 with the same content as today; the dashboard page needs at most 5 queries for 20 or 200 branches (today's 3, plus the session and the user).
- **AC15.** A test walks `reviewradar.urls.urlpatterns` and fails when a page other than `login` and `healthz` answers a visitor who is not signed in with anything but a redirect to `/login/`, so a new page cannot be left open by mistake.
- **AC16.** Tests in a new file `reviews/tests/integration/test_login_required.py`, every one marked `login`, cover AC11 to AC15.

Account block in the sidebar (T4):

- **AC17.** When signed in, the bottom of the sidebar shows "Signed in as <username>" with the username in `<strong>` carrying `data-sensitive`, and a "Sign out" button in a POST form to `/logout/` with a CSRF token, as on the design card.
- **AC18.** When nobody is signed in (the 404 page), the sidebar shows no account block and the page still renders.
- **AC19.** At phone width (360px) the account block wraps under the nav row, with no sideways scrolling.
- **AC20.** Tests in a new file `reviews/tests/integration/test_sidebar_account.py` cover AC17 and AC18.

Accounts and the demo user (T5):

- **AC21.** `uv run python manage.py create_user <username>` asks for the password twice without echo, checks it with Django's password validators, and creates an active user who is not staff. It prints `Created user <username>.` It refuses with one line and exit code 1 when the username exists, the two passwords differ, or a validator fails.
- **AC22.** When `REVIEWRADAR_DEMO_PASSWORD` is set and not empty, `seed_demo_data` creates the user `demo` with that password, or sets that password when `demo` exists, and prints `Demo user: demo`. When it is unset or empty it prints `REVIEWRADAR_DEMO_PASSWORD is not set; no demo user.` and goes on. It never deletes or changes another user, and the password is never printed.
- **AC23.** `render.yaml` lists the env var `REVIEWRADAR_DEMO_PASSWORD` with `sync: false`, so its value is typed in the Render dashboard and never stored in the repository.
- **AC24.** The README has a "Sign in" section: pages need an account; `create_user` to add one; `changepassword` to reset one; the demo user and `REVIEWRADAR_DEMO_PASSWORD`, locally and on Render.
- **AC25.** Tests in a new file `reviews/tests/integration/test_accounts.py` cover AC21 and AC22 (the password prompt is patched, no network).

Live result, checked by the owner after the release of the epic:

- **AC26.** On Render the health check on `/healthz/` passes, `/dashboard/` sends a visitor to the sign-in page, and the owner can sign in as `demo` with the password set in the Render dashboard.

## Edge cases

- Empty: a fresh database with no user; every page sends the visitor to `/login/` and no one can sign in until `create_user` is run (or the demo password is set and the seed runs).
- `next` pointing to another site: ignored, the user lands on `/dashboard/` (Django's own check).
- CSV and JSON for a visitor not signed in: a 302 to `/login/`, like the pages; no data is sent.
- Session length: Django's default (two weeks); signing out ends it.
- Large data: no new query per row; a signed-in page costs two more queries in total (AC14).
- Permissions: every signed-in user sees every business and branch; there is no staff-only page.
- Seed on Render: it runs at each start and deletes reviews, businesses and branches, never users; `demo` gets the current password each start.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Who creates accounts | The admin, with `manage.py create_user` | Django admin site; sign-up by visitors | Few users in the MVP; least code and no public sign-up form. |
| Q2 What a user can see | Every branch | Per business; roles per branch | One business in the data; scoping would touch every query and need a migration. Later epic. |
| Q3 Which pages need an account | All, except `/login/`, `/healthz/` and the 404 page | Only CSV and JSON | Review texts are customer data; locking by default is safer and uses Django's built-in middleware. |
| Q4 Forgotten password | Reset by the admin with `changepassword` | Reset link by email | No email service; a link would need SMTP and a secret on Render. |
| Q5 Demo on Render | User `demo`, password from `REVIEWRADAR_DEMO_PASSWORD` | `demo`/`demo` shown on the page; no demo user | No password in the repository, and the demo still works after each deploy. |
| Q6 Tests already on main | A hand-made `conftest.py` turns the login check off for them; new tests marked `login` check it | Change the hook and edit 12 test files | Old tests call `Client()` directly and count exact queries; signing them in adds two queries. The conftest keeps every guard. |
| Q7 Merging the epic | The owner approves each pull request; the tick merges | The tick merges epic pull requests by itself | Sign-in is a security change; each pull request gets a human look. Independent tasks run in parallel to shorten the waits. |
| Q8 Locking after wrong passwords | Not in this epic; follow-up | Lock 15 minutes after 5 failures | Few accounts, all made by the admin; keeps the epic small. |

## Design

`design/auth/README.md` (design card https://claude.ai/artifact/JLAyry3oArssECJLnAfzwx).

## Open questions
