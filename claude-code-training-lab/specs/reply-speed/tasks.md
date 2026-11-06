# Tasks: reply-speed

Two tasks. T2 depends on T1 only so that its screenshots show the demo numbers of AC8; the two share no file. The release and the check on the live site are done by the owner, outside these tasks.

## T1: Demo replies with realistic reply times

- **ACs:** AC1 to AC3
- **Files likely touched:** `reviews/management/commands/seed_demo_data.py`, `reviews/tests/integration/test_seed_demo_replies.py` (existing, may be updated: the count 6 becomes 9 and "good reviews only" becomes the rule of AC1 to AC3), `reviews/tests/integration/test_seed_demo_reply_times.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: "Replied in 24h" on the dashboard

- **ACs:** AC4 to AC11
- **Files likely touched:** `reviews/repositories.py`, `reviews/services.py`, `reviews/templates/reviews/dashboard.html`, `reviews/static/reviews/app.css`, `reviews/tests/unit/test_reply_speed.py` (NEW), `reviews/tests/integration/test_dashboard_reply_speed.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (a number the business reads, a dashboard query)
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` on a fresh demo database → `#kpi-reply-speed`, and `/dashboard/` → `#location-scores`
- **Label:** `agent:ready`, `area:app`

