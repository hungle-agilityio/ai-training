# Tasks: location-page

One epic issue, "Epic: location page with a weekly trend", holds the four tasks below as GitHub sub-issues and a checklist. The epic has no `agent:` label, so the loop never picks it, and no task says `Depends on` the epic. The owner closes the epic after the release (AC26).

Order: T1 and T2 start at once (no shared file). T3 waits for both. T4 waits for T1. T3 and T4 share no file and run side by side.

## T1: Location page

- **ACs:** AC1 to AC8
- **Files likely touched:** `reviewradar/urls.py`, `reviews/views.py`, `reviews/services.py`, `reviews/repositories.py`, `reviews/templates/reviews/location.html` (NEW), `reviews/static/reviews/app.css`, `reviews/tests/integration/test_location_page.py` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

## T2: Weekly trend numbers

- **ACs:** AC9 to AC14
- **Files likely touched:** `reviews/trend_service.py` (NEW), `reviews/trend_repository.py` (NEW), `reviews/tests/unit/test_weekly_trend.py` (NEW), `reviews/tests/integration/test_weekly_trend_query.py` (NEW)
- **Depends on:** none
- **Risk:** medium (dates and averages)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T3: Weekly trend chart on the location page

- **ACs:** AC15 to AC20
- **Files likely touched:** `reviews/views.py`, `reviews/templates/reviews/location.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_location_trend.py` (NEW)
- **Depends on:** T1 (the page), T2 (the numbers)
- **Risk:** low
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

## T4: Links to the location page

- **ACs:** AC21 to AC25
- **Files likely touched:** `reviews/services.py`, `reviews/templates/reviews/dashboard.html`, `reviews/templates/reviews/reviews.html`, `reviews/tests/integration/test_location_links.py` (NEW)
- **Depends on:** T1 (the `location` URL)
- **Risk:** low
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`
- **Note:** no change to `app.css` (T3 changes it at the same time); the links use the existing link styles.

AC26 is checked by the owner after the release of the whole epic.
