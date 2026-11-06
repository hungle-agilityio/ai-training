# Spec: csv-import

## Summary

A new page `/reviews/import/` lets a signed-in user upload a CSV file of reviews. The Reviews page gets an "Import CSV" button next to "Export CSV". The file has the same columns as Export CSV (`Location`, `Rating`, `Review text`, `Date`). Good rows become reviews, duplicates are skipped, bad rows are listed with their row number and reason, and a summary shows the counts. No migration; no other page changes except the new button.

## Definitions

- **Row number:** the line of the file as a spreadsheet shows it: the header is row 1, the first review is row 2.
- **Location match:** the `Location` cell, with spaces at both ends removed, equals a location name with letter case ignored. When two locations have the same name, the one with the lowest id is used.
- **Duplicate:** a row whose location, date (to the minute), rating and review text are all equal to an existing review, or to an earlier good row of the same file.
- **Vietnam time:** `Asia/Ho_Chi_Minh` (`rules/domain.md`), the time zone Export CSV writes.

## Acceptance criteria

Reading and checking the file (T1):

- **AC1.** The header row must contain the four columns `Location`, `Rating`, `Review text` and `Date`, in any order; letter case and spaces around a name are ignored, and other columns are ignored. When one or more are missing, nothing is saved and the message is "The file needs the columns Location, Rating, Review text and Date. Missing: <names>." with the missing names in that order, separated by ", ".
- **AC2.** The file is read as UTF-8, with or without the byte order mark that Export CSV writes. A file that is not valid UTF-8 is refused, nothing is saved, and the message is "Save the file as CSV UTF-8 and try again."
- **AC3.** A file larger than 1 MB (1,048,576 bytes), or with more than 2,000 rows after the header, is refused, nothing is saved, and the message is "The file is too large: at most 2,000 reviews and 1 MB." An empty file, or a file with only a header, is refused with "The file has no reviews." Blank lines (every cell empty) are skipped and not counted.
- **AC4.** `Rating` must be a whole number from 1 to 5 (spaces around it are ignored). Otherwise the row is an error "Rating must be a whole number from 1 to 5."
- **AC5.** `Date` must be "YYYY-MM-DD HH:MM" or "YYYY-MM-DD" (spaces around it are ignored), read as Vietnam time; a date alone means 00:00. Otherwise the row is an error "Date must look like 2026-11-06 14:30 or 2026-11-06." A date later than the moment of the import is an error "Date is in the future."
- **AC6.** `Location` must match a location (Definitions). Otherwise the row is an error "Location \"<cell>\" was not found." with the trimmed cell, cut to 60 characters. No location is created.
- **AC7.** `Review text` may be empty. Spaces at both ends are removed. When the text starts with a single quote followed by `=`, `+`, `-`, `@`, a tab or a carriage return (the guard Export CSV adds, `csv_safe`), that one quote is removed, so an exported file imports back with the same text. Text longer than 5,000 characters is an error "Review text is longer than 5,000 characters."
- **AC8.** A row with several problems shows only the first one, in the order Rating, Date, Location, Review text. The error list never shows the review text.
- **AC9.** Duplicates (Definitions) are skipped and counted; they are not errors.
- **AC10.** All good rows of one file are saved together in one transaction, each with `search_text` filled exactly as `repositories.create_review` does (`normalize_for_search`), so search finds imported reviews. Rows with errors do not stop the good rows.
- **AC11.** The service returns a frozen dataclass with `imported`, `duplicates` (both `int`), and `errors`: a list of (row number `int`, message `str`) in file order. The queries do not grow with each row: locations and possible duplicates are read with a fixed number of queries and the good rows are saved with `bulk_create`; the tests assert that importing 300 rows takes at most 10 queries.

The page (T2):

- **AC12.** The Reviews page `/reviews/` shows an "Import CSV" button (`id="import-csv"`) before "Export CSV" in its actions; it links to `/reviews/import/` (URL name `reviews-import`). The "Export CSV" button and its note do not change.
- **AC13.** `/reviews/import/` (GET) has the heading "Import reviews", the subtitle "Add reviews from a CSV file with the columns Location, Rating, Review text and Date.", a file field labelled "CSV file" that accepts `.csv`, a button "Import", a link "Download a sample file" to `reviews/import-sample.csv` (static), and a link "Back to reviews". The sidebar marks "Reviews" as the current item.
- **AC14.** The sample file has the header `Location,Rating,Review text,Date` and these 3 rows: `Downtown,5,Friendly staff and a short wait.,2026-11-01 09:30`; `Riverside,2,Could not get through on the phone.,2026-11-02 14:05`; `Airport,4,Clean rooms and kind nurses.,2026-11-03`. Imported on a fresh demo database it gives 3 imported, 0 duplicates, 0 errors; imported a second time, 0 imported and 3 duplicates.
- **AC15.** After a POST the same page shows the summary in a panel `id="import-result"`: "<n> reviews imported", "<n> duplicates skipped" and "<n> rows with errors" (singular "review", "duplicate", "row" for 1), and a link "See the reviews" to `/reviews/`. When there are errors, a table `id="import-errors"` with the columns "Row" and "Problem" lists at most the first 50; when there are more, a line "and <n> more rows with errors" follows. The file field is shown again for a next file.
- **AC16.** A refused file (AC1 to AC3) or a POST with no file shows the page with the message in a panel `id="import-error"` and the field marked invalid, and nothing is saved. With no file the message is "Choose a CSV file to import."
- **AC17.** The page needs sign-in like every page (visitors go to the sign-in page); the form uses the CSRF token; GET and POST only (other methods get 405). The view stays thin: a form in `reviews/import_forms.py` checks the file field, `reviews/import_service.py` does the rest.
- **AC18.** At 360 px the page does not scroll sideways; the error table scrolls inside its own box (`table-wrap`). It reuses the classes of `app.css` (`panel`, `panel-head`, `table`, `button`), in light and dark; no new CSS file.
- **AC19.** `reviews/views.py`, `reviews/forms.py`, `reviews/repositories.py`, `reviews/services.py`, `reviews/templates/reviews/base.html` and `reviews/static/reviews/app.css` do not change (they are being changed by other open tasks); `reviewradar/urls.py` gets one line.

## Edge cases

- Empty: a file with only a header (AC3). A file where every row is a duplicate: "0 reviews imported", "<n> duplicates skipped", "0 rows with errors".
- Every row bad: nothing saved, the counts and the error table show.
- Duplicate rows inside one file: the first is imported, the next ones are counted as duplicates (AC9).
- Large data: 2,000 rows never take one query per row (AC11); the file is read once, never kept after the request.
- Permissions: every signed-in user, as on the other pages (there are no roles).
- Security: the cells are only ever saved as data through the ORM and shown escaped by the template; no cell is used in a query string or a file path. The error list shows no customer text (AC8).
- Live demo site: imported reviews disappear when Render restarts the site (intent, Out of scope).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Feature | Import reviews from CSV | Sentiment by Claude; bad-review alert | First MVP item; no external service or migration, so the loop builds it all |
| Q2 Columns | Same as Export CSV, any order, case ignored, extra columns ignored | Exact order | An exported or hand-edited file imports without fuss |
| Q3 Unknown location | The row is an error | Create the location | A typo would create a wrong location silently |
| Q4 Some bad rows | Import the good rows, list the bad ones | Refuse the whole file; preview and confirm | One step, and the user fixes only the listed rows; duplicates are skipped, so re-importing the fixed file is safe |
| Q5 Duplicates | Skip and count | Import anyway | Importing the same file twice must not double the numbers |
| Q6 Date | "YYYY-MM-DD HH:MM" or "YYYY-MM-DD", Vietnam time, no future dates | Also DD/MM/YYYY | DD/MM and MM/DD cannot be told apart; the format matches Export CSV |
| Q7 Limits | 1 MB and 2,000 rows, UTF-8 | 5 MB and 10,000 rows | Enough for a branch's history; keeps one request short on the free plan |
| Q8 Empty text | Allowed | An error | Rating-only reviews exist on review sites |
| Q9 Entry point | "Import CSV" button on the Reviews page | Sidebar item | Next to Export CSV; `base.html` is being changed by #293 |
| Q10 Undo | Not in this version | "Undo last import" | Needs a migration; duplicates make a re-import safe |
| Q11 Sample file | A "Download a sample file" link | None | Shows the exact columns and date format |

## Design

`design/csv-import/README.md`

## Open questions
