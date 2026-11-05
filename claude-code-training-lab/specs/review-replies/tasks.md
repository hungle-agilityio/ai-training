# Tasks: review-replies

One epic issue, "Epic: reply to reviews", holds the six tasks below as GitHub sub-issues and a checklist. The epic has no `agent:` label, so the loop never picks it, and no task says `Depends on` the epic. The owner closes the epic after the release (AC33).

Order, chosen to exercise the loop:

- **Chain:** T1 → T2 → T3 → T5. T2 and T3 each say `Depends on` their direct parent only, so they can start on the parent's green pull request (#165) and stay open when the parent is merged (#180).
- **Side by side:** T6 starts once T1 is merged, beside T2. T4 starts once T2 is merged, beside T3. Neither shares a file with the task it runs beside.
- **Join:** T5 depends on T3 and T4 (it touches `services.py`, `repositories.py` and `forms.py`, which T4 and T3 also touch), so it starts after both are merged.

All tasks: no `.claude/` change, so `agent:ready`, `area:app`. New styles of the epic go in `reviews/static/reviews/replies.css` (made by T2), so T3 and T4 never share a stylesheet.

## T1: Reply data

- **ACs:** AC1 to AC7
- **Files likely touched:** `reviews/models.py`, `reviews/migrations/0004_reviewreply.py` (NEW), `reviews/reply_repository.py` (NEW), `reviews/reply_service.py` (NEW), `reviews/tests/unit/test_reply_text.py` (NEW), `reviews/tests/integration/test_reply_data.py` (NEW)
- **Depends on:** none
- **Risk:** medium (migration)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Reply drafts page

- **ACs:** AC8 to AC14
- **Files likely touched:** `reviewradar/urls.py`, `reviews/views.py`, `reviews/reply_service.py`, `reviews/reply_repository.py`, `reviews/templates/reviews/replies.html` (NEW), `reviews/templates/reviews/base.html`, `reviews/static/reviews/replies.css` (NEW), `reviews/tests/integration/test_replies_page.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (ordering, pagination)
- **needs-ui:** yes
- **Screens to capture:** `/replies/` → `#reply-queue`; `/replies/` → `.sidebar`
- **Label:** `agent:ready`, `area:app`

## T3: Reply page

- **ACs:** AC15 to AC22
- **Files likely touched:** `reviewradar/urls.py`, `reviews/views.py`, `reviews/forms.py`, `reviews/reply_service.py`, `reviews/templates/reviews/reply.html` (NEW), `reviews/templates/reviews/replies.html`, `reviews/static/reviews/replies.css`, `reviews/tests/integration/test_reply_page.py` (NEW)
- **Depends on:** T2
- **Risk:** medium (user input, a form that writes data)
- **needs-ui:** yes
- **Screens to capture:** `/reviews/1/reply/` (the first demo review, Airport, 2 stars, on a fresh demo database) → `#reply-form`; `/replies/` → `#reply-queue`
- **Label:** `agent:ready`, `area:app`

## T4: "Need a reply" on the dashboard

- **ACs:** AC23 to AC26
- **Files likely touched:** `reviews/services.py`, `reviews/repositories.py`, `reviews/templates/reviews/dashboard.html`, `reviews/static/reviews/app.css`, `reviews/tests/integration/test_dashboard_needs_reply.py` (NEW)
- **Depends on:** T2
- **Risk:** medium (a number the business reads, dashboard query count)
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` → `#kpi-needs-reply`; `/dashboard/` → `.kpis`
- **Label:** `agent:ready`, `area:app`

## T5: Reply status and filter on the review list

- **ACs:** AC27 to AC30
- **Files likely touched:** `reviews/services.py`, `reviews/repositories.py`, `reviews/forms.py`, `reviews/templates/reviews/reviews.html`, `reviews/static/reviews/replies.css`, `reviews/tests/integration/test_reviews_reply_status.py` (NEW)
- **Depends on:** T3, T4
- **Risk:** medium (filters, list queries)
- **needs-ui:** yes
- **Screens to capture:** `/reviews/` → `.reviews-table`; `/reviews/?reply=no` → `#filter-reply`
- **Label:** `agent:ready`, `area:app`

## T6: Demo replies

- **ACs:** AC31, AC32
- **Files likely touched:** `reviews/management/commands/seed_demo_data.py`, `reviews/tests/integration/test_seed_demo_replies.py` (NEW)
- **Depends on:** T1
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

AC33 is checked by the owner after the release of the whole epic.
