# Business rules

Rules found through implementation. Mark each one **Confirmed** (the business said so) or **Uncertain** (our assumption; ask). Not auto-loaded: `/plan` and `/review` read it; `/learn` writes it.

## Confirmed

- A branch's score is the average rating, one decimal, rounded half up (2.25 is 2.3). A branch with no reviews has no score.
- A week is Monday to Sunday in Vietnam time.
- Searching review text: every letter ignores case, including letters with accents (`NHÂN` finds "nhân"). Accents still count (`dau` does not find "đau"). A search finds any part of the text, and when several words are typed every one must appear, in any order. The shortest search is 3 characters, counted after trimming and collapsing spaces; the longest is 100 (a longer text is cut, without a message). `%` and `_` are searched as typed.
- A search typed by a manager can be a customer's name or phone number: the app never writes it to its own logs. It stays in the page address, so the web server's access logs do record it; the team handles those separately.

## Uncertain

- Case folding goes a little further than "small letters" outside Vietnamese: `STRASSE` finds "Straße", and `İSTANBUL` does not find "istanbul". Ask whether other languages matter.
- The production database is not known (only SQLite is configured). The search was built to work on any database; confirm which one runs in production.
