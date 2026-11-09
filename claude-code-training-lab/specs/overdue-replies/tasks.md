# Tasks: overdue-replies

Three tasks in one epic. T2 needs T1's data. T3 reads its number from the dashboard totals, not from T1's code; it depends on T1 on purpose, so this epic also tests two stacked children of one parent on the epic branch (ADR-021). T2 and T3 share no file and are built side by side. No existing test changes. The release and the check on the live site are done by the owner, outside these tasks.

## T1: Overdue rule and data

- **ACs:** AC1 to AC3
- **Files likely touched:** `reviews/reply_repository.py`, `reviews/reply_service.py`, `reviews/tests/unit/test_overdue_rule.py` (NEW), `reviews/tests/integration/test_overdue_replies_data.py` (NEW)
- **Depends on:** none
- **Risk:** medium (a rule the business reads, a list query)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Overdue label and filter on Reply drafts

- **ACs:** AC4 to AC10, AC13 (Reply drafts part), AC14 (`is_overdue`)
- **Files likely touched:** `reviews/forms.py`, `reviews/views.py`, `reviews/templates/reviews/replies.html`, `reviews/static/reviews/replies.css`, `reviews/tests/integration/test_replies_overdue.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (filter and pagination)
- **needs-ui:** yes
- **Screens to capture:** `/replies/` on a fresh demo database → `#reply-queue`; `/replies/?overdue=1` → `#reply-queue`
- **Label:** `agent:ready`, `area:app`

## T3: Overdue line on the dashboard

- **ACs:** AC11, AC12, AC13 (dashboard part), AC14 (`overdue_count`)
- **Files likely touched:** `reviews/services.py`, `reviews/templates/reviews/dashboard.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_dashboard_overdue.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (a number the business reads, a dashboard query)
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` on a fresh demo database → `#kpi-needs-reply`
- **Label:** `agent:ready`, `area:app`
