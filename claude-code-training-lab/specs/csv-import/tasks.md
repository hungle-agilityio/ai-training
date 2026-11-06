# Tasks: csv-import

Two tasks. T2 depends on T1 because the page calls the service. Both are built by the loop (`agent:ready`): every file is under `reviews/` or `reviewradar/`, no existing test changes, and no file of the open tasks #283, #291, #293, #294 is touched except one line in `reviewradar/urls.py`.

## T1: Read, check and save a CSV file of reviews

- **ACs:** AC1 to AC11
- **Files likely touched:** `reviews/import_service.py` (NEW), `reviews/import_repository.py` (NEW), `reviews/tests/unit/test_import_service.py` (NEW), `reviews/tests/integration/test_import_repository.py` (NEW)
- **Depends on:** none
- **Risk:** medium (input from users, numbers the business reads)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: Import page and "Import CSV" button

- **ACs:** AC12 to AC19
- **Files likely touched:** `reviews/import_views.py` (NEW), `reviews/import_forms.py` (NEW), `reviewradar/urls.py`, `reviews/templates/reviews/import.html` (NEW), `reviews/templates/reviews/reviews.html`, `reviews/static/reviews/import-sample.csv` (NEW), `reviews/tests/integration/test_import_page.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (file upload from users)
- **needs-ui:** yes
- **Screens to capture:** `/reviews/` → `#import-csv`; `/reviews/import/`; `/reviews/import/` after uploading the sample file twice → `#import-result`
- **Label:** `agent:ready`, `area:app`
