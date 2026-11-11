# Tasks: bad-review-follow-up

Five tasks in one epic, all `agent:ready`, built on the epic branch and merged there by the tick (ADR-022). T1 and T2 are independent (T2 has the migration, so the tick may run it alone). T3 and T4 both need T1 and T2 and can run side by side: they share no file. T5 needs T4 (its link opens T4's filter, and both change `reviews/services.py` and `reviews/repositories.py`). Parallel tasks never share a file.

## Query budget

| Page | Queries on main | After T1 | After T2 | After T3 | After T4 | After T5 |
|---|---|---|---|---|---|---|
| `/reviews/1/reply/` GET | 2 | 2 | 2 | 2 | 2 | 2 |
| `/reviews/1/follow-up/` POST | – | – | – | 5 | 5 | 5 |
| `/reviews/` GET | 3 | 3 | 3 | 3 | 3 | 3 |
| `/dashboard/` GET | 3 | 3 | 3 | 3 | 3 | 3 |

No query cap on `main` changes. The caps that must keep passing: `reviews/tests/integration/test_reply_page.py::test_get_makes_one_query` (2), `reviews/tests/integration/test_reviews_page.py` (3, two tests), and the dashboard caps of exactly 3 in `test_dashboard.py`, `test_dashboard_goals.py`, `test_dashboard_overdue.py`, `test_dashboard_needs_reply.py` and `test_dashboard_reply_speed.py`. T3 adds the cap of the follow-up post; no later task changes it.

## T1: Follow-up rule

- **ACs:** AC1, AC2, AC3, AC18
- **Files likely touched:** `reviews/followup.py` (NEW), `reviews/tests/unit/test_followup_rule.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Store cases, demo cases

- **ACs:** AC4, AC5, AC6, AC18
- **Files likely touched:** `reviews/models.py`, `reviews/migrations/0007_reviewfollowup.py` (NEW), `reviews/followup_repository.py` (NEW), `reviews/management/commands/seed_demo_data.py`, `reviews/tests/integration/test_followup_repository.py` (NEW), `reviews/tests/integration/test_seed_demo_followups.py` (NEW)
- **Depends on:** none
- **Risk:** medium (migration)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T3: Follow-up box on the reply page

- **ACs:** AC7, AC8, AC9, AC10, AC11, AC18
- **Files likely touched:** `reviews/followup_forms.py` (NEW), `reviews/views.py`, `reviewradar/urls.py`, `reviews/reply_repository.py`, `reviews/reply_service.py`, `reviews/templates/reviews/reply.html`, `reviews/static/reviews/replies.css`, `reviews/tests/integration/test_reply_followup.py` (NEW)
- **Depends on:** T1, T2
- **Risk:** medium (input from users)
- **needs-ui:** yes
- **Screens to capture:** the reply page of the demo review "Phone line always busy, could not book." → `#followup`
- **Label:** `agent:ready`, `area:app`

## T4: Follow-up filter and badge on the Reviews page

- **ACs:** AC12, AC13, AC14, AC15, AC18
- **Files likely touched:** `reviews/forms.py`, `reviews/services.py`, `reviews/repositories.py`, `reviews/templates/reviews/reviews.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_reviews_followup_filter.py` (NEW)
- **Depends on:** T1, T2
- **Risk:** medium (filters, list query)
- **needs-ui:** yes
- **Screens to capture:** `/reviews/?followup=open` → `main`
- **Label:** `agent:ready`, `area:app`

## T5: Open cases on the dashboard

- **ACs:** AC16, AC17, AC18
- **Files likely touched:** `reviews/services.py`, `reviews/repositories.py`, `reviews/templates/reviews/dashboard.html`, `reviews/tests/integration/test_dashboard_open_cases.py` (NEW)
- **Depends on:** T4
- **Risk:** medium (dashboard query, a number the business reads)
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` → `#kpi-open-cases`
- **Label:** `agent:ready`, `area:app`
