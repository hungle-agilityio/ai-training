# Tasks: reply-templates

Five tasks in one epic, all `agent:ready`, built on the epic branch and merged there by the tick (ADR-022). T1 and T2 are independent (T2 has the migration, so the tick may run it alone). T3 and T5 both need T1 and T2 and can run side by side. T4 needs T3. Parallel tasks never share a file.

## Query budget

| Page | Queries on main | After T1 | After T2 | After T3 | After T4 | After T5 |
|---|---|---|---|---|---|---|
| `/settings/` GET | 3 | 3 | 3 | 4 | 4 | 4 |
| `/settings/templates/<id>/` GET | – | – | – | – | 3 | 3 |
| `/settings/templates/<id>/delete/` GET | – | – | – | – | 3 | 3 |
| `/reviews/<id>/reply/` GET | 1 | 1 | 1 | 1 | 1 | 2 |
| `/reviews/<id>/reply/` POST suggest | 2 | 2 | 2 | 2 | 2 | 3 |
| `/reviews/<id>/reply/` POST use template | – | – | – | – | – | 3 |

Query caps on `main` that change: `/settings/` in `reviews/tests/integration/test_settings_page.py::test_get_makes_at_most_two_queries` and `reviews/tests/integration/test_settings_suggestions.py::test_settings_page_makes_at_most_two_queries` (3 → 4, T3); the reply page in `reviews/tests/integration/test_reply_page.py::test_get_makes_one_query` (1 → 2, T5) and `reviews/tests/integration/test_reply_suggest_page.py::test_suggest_makes_at_most_two_queries_and_one_call` (2 → 3, T5). T4 adds its own caps for its new pages; no later task changes them.

## T1: Template rule

- **ACs:** AC1, AC2, AC3, AC4, AC21
- **Files likely touched:** `reviews/reply_templates.py` (NEW), `reviews/tests/unit/test_reply_template_rule.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Store templates, demo templates

- **ACs:** AC5, AC6, AC7, AC21
- **Files likely touched:** `reviews/models.py`, `reviews/migrations/0006_replytemplate.py` (NEW), `reviews/template_repository.py` (NEW), `reviews/management/commands/seed_demo_data.py`, `reviews/tests/integration/test_template_repository.py` (NEW), `reviews/tests/integration/test_seed_demo_templates.py` (NEW)
- **Depends on:** none
- **Risk:** medium (migration)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T3: Reply templates on Settings

- **ACs:** AC8, AC9, AC10, AC11, AC21
- **Files likely touched:** `reviews/template_forms.py` (NEW), `reviews/template_views.py` (NEW), `reviews/goal_views.py`, `reviewradar/urls.py`, `reviews/templates/reviews/settings.html`, `reviews/static/reviews/settings.css`, `reviews/tests/integration/test_settings_templates.py` (NEW)
- **Existing tests that change:** `test_settings_page.py::test_get_makes_at_most_two_queries` and `test_settings_suggestions.py::test_settings_page_makes_at_most_two_queries` (cap 3 → 4)
- **Depends on:** T1, T2
- **Risk:** medium (input from users)
- **needs-ui:** yes
- **Screens to capture:** `/settings/` → `#settings-templates`
- **Label:** `agent:ready`, `area:app`

## T4: Edit and delete a template

- **ACs:** AC12, AC13, AC14, AC15, AC21
- **Files likely touched:** `reviews/template_views.py`, `reviewradar/urls.py`, `reviews/templates/reviews/template_edit.html` (NEW), `reviews/templates/reviews/template_delete.html` (NEW), `reviews/tests/integration/test_template_edit.py` (NEW)
- **Depends on:** T3
- **Risk:** medium (input from users, delete)
- **needs-ui:** yes
- **Screens to capture:** the edit page of the demo template "Thank you" → `main`
- **Label:** `agent:ready`, `area:app`

## T5: Template picker on the reply page

- **ACs:** AC16, AC17, AC18, AC19, AC20, AC21
- **Files likely touched:** `reviews/views.py`, `reviews/forms.py`, `reviews/reply_service.py`, `reviews/templates/reviews/reply.html`, `reviews/static/reviews/replies.css`, `reviews/tests/integration/test_reply_template_picker.py` (NEW)
- **Existing tests that change:** `test_reply_page.py::test_get_makes_one_query` (cap 1 → 2) and `test_reply_suggest_page.py::test_suggest_makes_at_most_two_queries_and_one_call` (cap 2 → 3)
- **Depends on:** T1, T2
- **Risk:** medium (input from users)
- **needs-ui:** yes
- **Screens to capture:** the reply page of a bad demo review → `#reply-template`
- **Label:** `agent:ready`, `area:app`
