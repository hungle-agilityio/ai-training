# Tasks: locations-settings

Five tasks in one epic, all `agent:ready`, built on the epic branch and merged there by the tick (ADR-022). T1 and T2 are independent and run side by side. T3 needs T1 and T2. T4 and T5 need T3 and can run side by side: they share no file. No migration.

## Query budget

| Page | Queries on main | After T1 | After T2 | After T3 | After T4 | After T5 |
|---|---|---|---|---|---|---|
| `/settings/` GET | 4 | 4 | 4 | 4 | 4 | 4 |
| `/settings/locations/1/` GET | – | – | – | – | 3 | 3 |
| `/settings/locations/1/` POST | – | – | – | – | 5 | 5 |
| `/dashboard/` GET | 3 | 3 | 3 | 3 | 3 | 3 |

No query cap on `main` changes. The caps that must keep passing: `reviews/tests/integration/test_settings_page.py::test_get_makes_at_most_two_queries`, `reviews/tests/integration/test_settings_suggestions.py::test_settings_page_makes_at_most_two_queries` and `reviews/tests/integration/test_settings_templates.py` (4), and the dashboard caps of exactly 3. T4 adds the caps of its new page; no later task changes them.

## T1: Location name rule

- **ACs:** AC1, AC2, AC3, AC14
- **Files likely touched:** `reviews/location_names.py` (NEW), `reviews/tests/unit/test_location_name_rule.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Add and rename in the repository

- **ACs:** AC4, AC5, AC14
- **Files likely touched:** `reviews/location_repository.py` (NEW), `reviews/tests/integration/test_location_repository.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T3: Locations panel on Settings

- **ACs:** AC6, AC7, AC8, AC9, AC14
- **Files likely touched:** `reviews/location_forms.py` (NEW), `reviews/location_views.py` (NEW), `reviews/goal_views.py`, `reviewradar/urls.py`, `reviews/templates/reviews/settings.html`, `reviews/static/reviews/settings.css`, `reviews/tests/integration/test_settings_locations.py` (NEW)
- **Depends on:** T1, T2
- **Risk:** medium (input from users)
- **needs-ui:** yes
- **Screens to capture:** `/settings/` → `#settings-locations`
- **Label:** `agent:ready`, `area:app`

## T4: Rename a location

- **ACs:** AC10, AC11, AC12, AC14
- **Files likely touched:** `reviews/location_views.py`, `reviewradar/urls.py`, `reviews/templates/reviews/location_rename.html` (NEW), `reviews/tests/integration/test_location_rename.py` (NEW)
- **Depends on:** T3
- **Risk:** medium (input from users)
- **needs-ui:** yes
- **Screens to capture:** the rename page of the demo location "Downtown" → `main`
- **Label:** `agent:ready`, `area:app`

## T5: Add-a-location link on the empty dashboard

- **ACs:** AC13, AC14
- **Files likely touched:** `reviews/templates/reviews/dashboard.html`, `reviews/tests/integration/test_dashboard_add_location.py` (NEW)
- **Depends on:** T3
- **Risk:** low
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` with no locations → `main`
- **Label:** `agent:ready`, `area:app`
