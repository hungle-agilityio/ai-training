# Tasks: score-goals

Five tasks in one epic, all `agent:ready`, built on the epic branch and merged there by the tick (ADR-022). T1 and T2 are independent and run side by side. T3 needs T2. T4 needs T1 and T2 and can run beside T3 or T5. T5 needs T1 and T3 (both change `reviews/views.py`, so T5 waits for T3). Parallel tasks never share a file. No existing test changes.

## T1: Goal rule

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC17
- **Files likely touched:** `reviews/goals.py` (NEW), `reviews/tests/unit/test_goal_rule.py` (NEW)
- **Depends on:** none
- **Risk:** medium (a number the business reads)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Store goals, demo goals

- **ACs:** AC6, AC7, AC8, AC17
- **Files likely touched:** `reviews/models.py`, `reviews/migrations/0005_branch_target_score.py` (NEW), `reviews/goal_repository.py` (NEW), `reviews/management/commands/seed_demo_data.py`, `reviews/tests/integration/test_goal_repository.py` (NEW), `reviews/tests/integration/test_seed_demo_goals.py` (NEW)
- **Depends on:** none
- **Risk:** medium (migration)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T3: Location goals on Settings

- **ACs:** AC9, AC10, AC11, AC12, AC17
- **Files likely touched:** `reviews/goal_forms.py` (NEW), `reviews/goal_views.py` (NEW), `reviews/views.py`, `reviewradar/urls.py`, `reviews/templates/reviews/settings.html`, `reviews/static/reviews/settings.css`, `reviews/tests/integration/test_settings_goals.py` (NEW)
- **Depends on:** T2
- **Risk:** medium (input from users)
- **needs-ui:** yes
- **Screens to capture:** `/settings/` → `#settings-goals`
- **Label:** `agent:ready`, `area:app`

## T4: Goal column on the dashboard

- **ACs:** AC13, AC14, AC17
- **Files likely touched:** `reviews/services.py`, `reviews/repositories.py`, `reviews/templates/reviews/dashboard.html`, `reviews/tests/integration/test_dashboard_goals.py` (NEW)
- **Depends on:** T1, T2
- **Risk:** medium (dashboard query count)
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` → `#location-scores`
- **Label:** `agent:ready`, `area:app`

## T5: Goal panel on the location page

- **ACs:** AC15, AC16, AC17
- **Files likely touched:** `reviews/views.py`, `reviews/templates/reviews/location.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_location_goal.py` (NEW)
- **Depends on:** T1, T3
- **Risk:** low
- **needs-ui:** yes
- **Screens to capture:** the Downtown location page `/locations/<Downtown id>/` → `#location-goal`
- **Label:** `agent:ready`, `area:app`
