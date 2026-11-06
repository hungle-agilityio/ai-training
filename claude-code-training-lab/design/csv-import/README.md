# Design: csv-import

Design card: https://claude.ai/artifact/SLy66hVRimZCRPrb3wNuqt

Five boards (demo data only):

1. **Reviews page:** an "Import CSV" button (`#import-csv`) before "Export CSV"; the export button and its note stay as they are (AC12).
2. **Import page, normal:** heading "Import reviews", the subtitle of AC13, the "CSV file" field, the "Import" button, the links "Download a sample file" and "Back to reviews"; the sample file of AC14.
3. **After an import with some wrong rows:** `#import-result` with "3 reviews imported", "1 duplicate skipped", "2 rows with errors", the `#import-errors` table (Row 4 "Rating must be a whole number from 1 to 5.", Row 6 "Location \"Airprot\" was not found.") and the link "See the reviews"; the form below for the next file (AC15).
4. **Refused file:** `#import-error` with "Save the file as CSV UTF-8 and try again." and the field marked invalid; the other messages of AC1 to AC3 and AC16 use the same panel.
5. **Narrow, 360 px:** the counts wrap, the error table scrolls inside its box, no sideways page scroll (AC18).

The build uses the texts of `specs/csv-import/spec.md` and the classes of `app.css` (`panel`, `table`, `table-wrap`, `button`), in light and dark; no new CSS file. The dashed pink outline only marks what is new.
