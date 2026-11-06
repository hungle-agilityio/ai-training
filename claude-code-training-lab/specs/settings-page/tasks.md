# Tasks: settings-page

Three tasks. T2 builds on T1 (same template) and on #282 (`reply_suggestion.suggestion_mode()`). T3 is the release of the epic, done by the owner's release command, so it is `agent:manual`. No task changes `pyproject.toml`, `uv.lock` or `.claude/`, and none adds a migration.

## T1: Settings page with change password

- **ACs:** AC1 to AC10
- **Files likely touched:** `reviewradar/urls.py`, `reviews/views.py`, `reviews/forms.py`, `reviews/templates/reviews/base.html`, `reviews/templates/reviews/settings.html` (NEW), `reviews/static/reviews/settings.css` (NEW), `reviews/tests/integration/test_settings_page.py` (NEW), `reviews/tests/integration/test_replies_page.py` (one assertion, see below)
- **Existing tests that change:** `reviews/tests/integration/test_replies_page.py::test_sidebar_item_is_an_active_link_without_soon`: the line `assert page.count("is-disabled") == 1  # Settings only` becomes `assert page.count("is-disabled") == 0`; nothing else in that file changes.
- **Depends on:** none
- **Risk:** medium (passwords, user input)
- **needs-ui:** yes
- **Screens to capture:** `/settings/` → `#settings-account`; `/settings/?saved=1` → `#settings-account`
- **Label:** `agent:ready`, `area:app`

## T2: Reply suggestions panel on the Settings page

- **ACs:** AC11 to AC14
- **Files likely touched:** `reviews/settings_service.py` (NEW), `reviews/views.py`, `reviews/templates/reviews/settings.html`, `reviews/tests/unit/test_settings_service.py` (NEW), `reviews/tests/integration/test_settings_suggestions.py` (NEW)
- **Depends on:** T1, #282
- **Risk:** low
- **needs-ui:** yes
- **Screens to capture:** `/settings/` (fresh demo database, DEBUG on, no key, so the panel shows Demo) → `#settings-suggestions`
- **Label:** `agent:ready`, `area:app`

## T3: Release the Settings page epic to Render

- **ACs:** AC15
- **Files likely touched:** none (the release only moves branches and a tag)
- **Depends on:** T1, T2
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual`, `area:app` (format of #278)
