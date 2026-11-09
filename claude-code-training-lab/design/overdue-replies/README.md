# Design: overdue-replies

Design card: https://claude.ai/artifact/8wCjBAy4pAANn5yT4sxCSv

Five boards, demo data from `seed_demo_data` right after a restart:

1. **Normal, Reply drafts "All":** tabs "All" (active) and "Overdue only" above the count line "5 reviews need a reply". Airport 1★ "Billing mistake and nobody called back." has the "Overdue" badge next to the stars; Airport 2★ "Waited 50 minutes, nobody apologized." (created now) has none (AC4, AC6, AC13).
2. **Reply drafts "Overdue only":** "1 overdue review needs a reply", one row with the badge, "Showing 1-1 of 1 reviews" (AC7, AC13).
3. **Empty "Overdue only":** "No overdue reviews", "Every bad review older than 24 hours has a reply.", link "Show all reviews" (AC8).
4. **Dashboard "Need a reply":** demo data shows 5 and the link "1 overdue (bad, over 24 h)" in `--bad`; with none overdue the muted line "None overdue" (AC11, AC13).
5. **Narrow, 360 px:** the tabs wrap, the table scrolls inside its box as today, no sideways page scroll (AC10).

The badge is `--bad` text on `--bad-soft`, the active tab `--brand` on `--brand-soft`, all from `app.css`, in light and dark. The dashed pink outline only marks what is new.
