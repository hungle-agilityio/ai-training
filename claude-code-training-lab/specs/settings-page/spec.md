# Spec: settings-page

## Summary

The sidebar item "Settings" stops being a disabled "Soon" item and links to a new page `/settings/`. The page has two panels. "Account" shows the username and a form to change one's own password with Django's `PasswordChangeForm` (current password, new password twice, Django's four password validators); the user stays signed in and their other sessions are signed out. "Reply suggestions" shows, read-only, whether the "Suggest a reply" button of epic #281 is on, in demo mode or off, and the model it uses; it never shows the API key. No model, no migration, no new package. The live site changes at the release task of this epic (ADR-017).

## Acceptance criteria

Settings page and password (T1):

- **AC1.** `GET /settings/` (URL name `settings`) answers 200 for a signed-in user with the template `reviews/settings.html` built on `reviews/base.html`: title `Settings · ReviewRadar`, heading `Settings`, subtitle `Your account and how ReviewRadar is set up.`, and no "Export JSON" button. A visitor who is not signed in gets a 302 to `/login/?next=/settings/` (the existing `LoginRequiredMiddleware`).
- **AC2.** In the sidebar of every page, "Settings" is a link `<a class="nav-item" href="/settings/">` with its gear icon and without `<em>Soon</em>`; on `/settings/` it has `is-active` and `aria-current="page"`. No page has an item with `is-disabled` any more.
- **AC3.** A panel `id="settings-account"` with the heading `Account` shows `Username` and the signed-in user's username inside an element with `data-sensitive`, then the line `To change your username, ask your ReviewRadar admin.`
- **AC4.** In the same panel, under the heading `Change password`, a POST form to `/settings/` with a CSRF token and three password fields, in this order: `Current password` (`old_password`, `autocomplete="current-password"`), `New password` (`new_password1`, `autocomplete="new-password"`), `Confirm new password` (`new_password2`, `autocomplete="new-password"`), the hint `At least 8 characters, not only numbers, not a common password and not like your username.`, and the button `Change password`. The form is `django.contrib.auth.forms.PasswordChangeForm` for `request.user`; the view holds no rule of its own.
- **AC5.** A valid POST sets the new password, keeps the current session signed in (`update_session_auth_hash`), so the user's other sessions are signed out (Django's session hash), and redirects (302) to `/settings/?saved=1`. That page shows `Password changed.` in an element `id="password-saved"` with `role="status"`. `?saved=` with any other value shows nothing (read by a form in `reviews/forms.py`, as `SavedForm` does today).
- **AC6.** An invalid POST answers 200 on the same page with Django's messages next to their fields: a wrong current password gives `Your old password was entered incorrectly. Please enter it again.`, two different new passwords give Django's "The two password fields didn’t match.", and a validator failure gives that validator's message (for example `This password is too short. It must contain at least 8 characters.`). The password is not changed, and the three fields are empty in the answer (no password is ever written into the page).
- **AC7.** A POST without the CSRF token answers 403. Methods other than GET and POST answer 405.
- **AC8.** `GET /settings/` for a signed-in user makes at most 2 database queries (the session and the user).
- **AC9.** At 360px wide the panels stack, the fields take the full width and the page does not scroll sideways. New styles go in a new file `reviews/static/reviews/settings.css`, linked from `reviews/settings.html` only.
- **AC10.** Tests in a new file `reviews/tests/integration/test_settings_page.py` cover AC1 to AC8 (the sign-in tests are marked `login`). The one existing assertion that counts `is-disabled` changes as listed in the issue under `## Existing tests that change`; no other existing test changes.

Reply suggestions panel (T2):

- **AC11.** A new module `reviews/settings_service.py` has `suggestion_status() -> SuggestionStatus`, a frozen dataclass `SuggestionStatus(mode: Literal["live", "fake", "off"], label: str, detail: str, model: str | None)` built from `reply_suggestion.suggestion_mode()` (#282) and `settings.ANTHROPIC_MODEL`:
  - `"live"`: label `On`, detail `Staff can ask Claude for a reply draft on each review's reply page.`, model = the model name.
  - `"fake"`: label `Demo`, detail `No API key: the button gives a fixed sample draft and nothing is sent to Claude.`, model `None`.
  - `"off"`: label `Off`, detail `The "Suggest a reply" button is hidden. Your ReviewRadar admin can turn it on.`, model `None`.
  It makes no database query and no network call.
- **AC12.** Below the Account panel, a panel `id="settings-suggestions"` with the heading `Reply suggestions` shows the label as a badge (`badge-positive` for On, `badge-watch` for Demo, `badge-neutral` for Off), the detail line, and, only for On, the line `Model: <model>` (for example `Model: claude-haiku-5-5`). The page never contains the value of `ANTHROPIC_API_KEY`, in any mode.
- **AC13.** `GET /settings/` still makes at most 2 database queries (AC8).
- **AC14.** Tests in new files `reviews/tests/unit/test_settings_service.py` and `reviews/tests/integration/test_settings_suggestions.py` cover AC11 to AC13 for each mode (settings overridden with pytest-django's `settings` fixture, a fake key such as `sk-test-not-real` that must not appear in the page), never the network.

Release (T3):

- **AC15.** After the merge of T1 and T2, `ops/release.py` releases the epic. On Render, signed in as `demo`: "Settings" in the sidebar opens `/settings/` and shows `demo`; a wrong current password shows the error of AC6; the Reply suggestions panel shows `On` and the model when `ANTHROPIC_API_KEY` is set on Render, otherwise `Off`.

## Edge cases

- Empty: no reply suggestion setup gives the `Off` panel (AC11); the Account panel always has a user, because the page needs sign-in.
- Large data: the page reads no reviews or branches; its query count does not depend on the data (AC8).
- Permissions: every signed-in user sees the page and changes only their own password; nobody can see or change another user's account here.
- The demo account on Render: whoever signs in as `demo` can change its password; `seed_demo_data` sets it back to `REVIEWRADAR_DEMO_PASSWORD` at the next start (spec `auth` AC22).
- Other devices: after a change, the user's other sessions are signed out and go to `/login/` on their next page.
- A browser that fills a saved password: the `autocomplete` values of AC4 let password managers offer the right entries.
- The service of #282 not merged yet: T2 waits for it (Depends on #282).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Scope of version 1 | Account (username + change password) and a read-only Reply suggestions panel | Location management; signature per location; password only | Fills today's real gap, no migration, no overlap with #282 and #283 |
| Q2 Change password | Current, new and confirm with Django's `PasswordChangeForm` and its validators; stay signed in, other sessions signed out | No current password | Django's tested form; the current password stops someone at an unlocked screen |
| Q3 Profile fields | None editable; username shown read-only | Display name and e-mail | Nothing in the app uses them yet |
| Q4 Who sees Settings | Every signed-in user, own account only | Staff only | No staff role exists; each user manages only their own password |
| Q5 Reply suggestions panel | Read-only status On / Demo / Off and the model, never the key; depends on #282 | Leave it out | Staff learn why the button is hidden; settings stay environment variables |
| Q6 Lock after wrong passwords | No (follow-up) | Lock 15 minutes after 5 failures | Same choice as spec `auth` Q8; keeps the epic small |
| Q7 After a successful change | Stay on `/settings/` with "Password changed." | Go to the dashboard | The user sees the result where they acted |
| Q8 Tasks | T1 page and password; T2 suggestions panel (after T1 and #282); T3 release | One task | Small pull requests; T2 waits only for what it needs; the owner wants a deploy task per epic |

## Design

Design card linked in `design/settings-page/README.md`.

## Open questions
