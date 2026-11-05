# Tasks: monthly-report

One epic issue, "Epic: monthly report", holds the five tasks below as GitHub sub-issues and a checklist. The epic has no `agent:` label, so the loop never picks it, and no task says `Depends on` the epic. The owner closes the epic after the release (AC26).

Order, chosen to exercise the loop:

- **Chain:** T1 → T2 → T3 → T5. Each task says `Depends on` its direct parent only, so it can start on its parent's green pull request (#165) and stays open when the parent is merged (#180).
- **Independent:** T4 starts at once, beside T1, and shares no file with any other task.

## T1: Monthly report numbers

- **ACs:** AC1 to AC6
- **Files likely touched:** `reviews/report_service.py` (NEW), `reviews/report_repository.py` (NEW), `reviews/tests/unit/test_monthly_report.py` (NEW), `reviews/tests/integration/test_monthly_report_query.py` (NEW)
- **Depends on:** none
- **Risk:** medium (dates and averages)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Monthly report page

- **ACs:** AC7 to AC14
- **Files likely touched:** `reviewradar/urls.py`, `reviews/views.py`, `reviews/forms.py`, `reviews/templates/reviews/reports.html` (NEW), `reviews/templates/reviews/base.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_reports_page.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (user input, a new page)
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

## T3: Change against the previous month

- **ACs:** AC15 to AC18
- **Files likely touched:** `reviews/report_service.py`, `reviews/templates/reviews/reports.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_reports_change.py` (NEW)
- **Depends on:** T2
- **Risk:** medium (a number the business reads)
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

## T4: Demo reviews over three months

- **ACs:** AC19, AC20
- **Files likely touched:** `reviews/management/commands/seed_demo_data.py`, `reviews/tests/integration/test_seed_demo_history.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T5: Monthly report CSV export

- **ACs:** AC21 to AC25
- **Files likely touched:** `reviewradar/urls.py`, `reviews/views.py`, `reviews/report_service.py`, `reviews/templates/reviews/reports.html`, `reviews/tests/integration/test_reports_export.py` (NEW)
- **Depends on:** T3
- **Risk:** low
- **needs-ui:** yes
- **Label:** `agent:ready`, `area:app`

AC26 is checked by the owner after the release of the whole epic.
