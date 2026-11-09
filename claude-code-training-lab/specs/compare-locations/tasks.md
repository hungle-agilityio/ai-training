# Tasks: compare-locations

Five tasks in one epic, all `agent:ready`, all built on the epic branch and merged there by the tick (spec `epic-review-once`). T1 → T2 → (T3 and T4 side by side, no shared file) → T5 after T4. No existing test changes.

## T1: Compare rule and data

- **ACs:** AC1, AC2, AC3, AC16
- **Files likely touched:** `reviews/compare_repository.py` (NEW), `reviews/compare_service.py` (NEW), `reviews/tests/unit/test_compare_rule.py` (NEW), `reviews/tests/integration/test_compare_data.py` (NEW)
- **Depends on:** none
- **Risk:** medium (numbers the business reads, one aggregated query)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Compare page

- **ACs:** AC4, AC5, AC6, AC7, AC8, AC16
- **Files likely touched:** `reviews/compare_forms.py` (NEW), `reviews/compare_views.py` (NEW), `reviews/templates/reviews/compare.html` (NEW), `reviewradar/urls.py`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_compare_page.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (filters from user input, query count)
- **needs-ui:** yes
- **Screens to capture:** `/compare/?a=<Downtown id>&b=<Riverside id>` → `#compare-table`; `/compare/` → `#compare-form`
- **Label:** `agent:ready`, `area:app`

## T3: Compare links in the sidebar and on the location page

- **ACs:** AC9, AC10, AC16
- **Files likely touched:** `reviews/templates/reviews/base.html`, `reviews/templates/reviews/location.html`, `reviews/tests/integration/test_compare_links.py` (NEW)
- **Depends on:** T2
- **Risk:** low
- **needs-ui:** yes
- **Screens to capture:** `/locations/<Riverside id>/` → `.topbar`; `/compare/` → `.sidebar`
- **Label:** `agent:ready`, `area:app`

## T4: Topics side by side

- **ACs:** AC11, AC12, AC13, AC16
- **Files likely touched:** `reviews/compare_service.py`, `reviews/compare_views.py`, `reviews/templates/reviews/compare.html`, `reviews/tests/integration/test_compare_topics.py` (NEW)
- **Depends on:** T2
- **Risk:** medium (dashboard-like queries)
- **needs-ui:** yes
- **Screens to capture:** `/compare/?a=<Downtown id>&b=<Riverside id>` → `#compare-topics`
- **Label:** `agent:ready`, `area:app`

## T5: Download the comparison as CSV

- **ACs:** AC14, AC15, AC16
- **Files likely touched:** `reviews/compare_service.py`, `reviews/compare_views.py`, `reviews/templates/reviews/compare.html`, `reviewradar/urls.py`, `reviews/tests/integration/test_compare_export.py` (NEW)
- **Depends on:** T4 (same files)
- **Risk:** medium (user input, file download)
- **needs-ui:** yes
- **Screens to capture:** `/compare/?a=<Downtown id>&b=<Riverside id>` → `.topbar`
- **Label:** `agent:ready`, `area:app`
