# ADR-007: Review search uses a stored normalised copy of the text

- Status: Accepted
- Date: 2026-10-22

## Context

Managers search reviews by words, with capital and small letters treated the same for every letter, accents kept (`dau` is not `đau`). The default query (`icontains`) and `Lower()` on SQLite fold only ASCII letters, and NFC and NFD forms of the same letter do not match. The production database is not known.

## Decision

`Review.search_text` keeps the text in one form (NFC, casefold, NFC), written by `repositories.create_review` and filled for old rows by a backfill migration. The search normalises the typed words the same way and filters with one `contains` per word, so every word must appear. Rejected: a Python function registered in SQLite (ties the code to one database), filtering in Python (breaks pagination and is slow), and relying on Postgres `ILIKE` (the production database is unverified).

## Consequences

- A review must be created and changed only through the repository; a change of the rule needs a new backfill migration.
- Every review stores its text twice. A search is `LIKE '%word%'`, which scans the table: fine now, revisit (full-text index) when the data grows.
- `reviews_newest_first` loads `search_text` although the page never shows it (`defer` is an open nit).
