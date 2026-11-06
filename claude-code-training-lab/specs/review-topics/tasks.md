# Tasks: review-topics

Six tasks, all built by the loop (`agent:ready`, `area:app`): every file is under `reviews/` or `reviewradar/`. T1 comes first. T2, T3, T5 and T6 depend only on T1 and share no file, so they can build in parallel on the epic branch. T4 depends on T3 because both change `reviews.html`. New tests go in new test files; the two existing tests that change are named in their task.

## T1: Topic rules and totals

- **ACs:** AC1 to AC5
- **Files likely touched:** `reviews/topics.py` (NEW), `reviews/topic_repository.py` (NEW), `reviews/topic_service.py` (NEW), `reviews/tests/unit/test_topics.py` (NEW), `reviews/tests/integration/test_topic_totals.py` (NEW)
- **Depends on:** none
- **Risk:** medium (numbers the business reads, query count)
- **needs-ui:** no

## T2: Topics page and sidebar item

- **ACs:** AC6 to AC11
- **Files likely touched:** `reviews/topic_views.py` (NEW), `reviews/topic_forms.py` (NEW), `reviews/templates/reviews/topics.html` (NEW), `reviewradar/urls.py`, `reviews/templates/reviews/base.html`, `reviews/tests/integration/test_topics_page.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (filters, numbers)
- **needs-ui:** yes. Screens: `/topics/` → `#topics-table`; `/topics/?period=30`.

## T3: Topic filter on the Reviews page

- **ACs:** AC12 to AC14
- **Files likely touched:** `reviews/forms.py`, `reviews/services.py`, `reviews/repositories.py`, `reviews/templates/reviews/reviews.html`, `reviews/tests/integration/test_reviews_topic_filter.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (filters, pagination links)
- **needs-ui:** yes. Screen: `/reviews/?topic=wait` → `.filters`.

## T4: Topic labels on each review

- **ACs:** AC15
- **Files likely touched:** `reviews/templatetags/topic_tags.py` (NEW), `reviews/templates/reviews/reviews.html`, `reviews/tests/integration/test_reviews_topic_labels.py` (NEW)
- **Depends on:** T3 (same template)
- **Risk:** low
- **needs-ui:** yes. Screen: `/reviews/` → `.reviews-table`.

## T5: Topics panel on the location page

- **ACs:** AC16 to AC18
- **Files likely touched:** `reviews/views.py` (the `location` view only), `reviews/templates/reviews/location.html`, `reviews/tests/integration/test_location_topics.py` (NEW), `reviews/tests/integration/test_location_page.py` (one line)
- **Existing tests that change:** `test_location_page.py::test_page_needs_at_most_four_queries`: `django_assert_max_num_queries(4)` becomes `(5)`.
- **Depends on:** T1
- **Risk:** medium (query count)
- **needs-ui:** yes. Screen: the first location → `#location-topics`.

## T6: Topics panel in the Monthly report

- **ACs:** AC19 to AC20
- **Files likely touched:** `reviews/report_service.py`, `reviews/templates/reviews/reports.html`, `reviews/tests/integration/test_reports_topics.py` (NEW), `reviews/tests/integration/test_reports_page.py` (one line)
- **Existing tests that change:** `test_reports_page.py::test_page_uses_one_query`: `django_assert_max_num_queries(1)` becomes `(2)`.
- **Depends on:** T1
- **Risk:** medium (numbers, months, query count)
- **needs-ui:** yes. Screen: `/reports/` → `#report-topics`.
