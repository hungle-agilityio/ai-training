# Design: monthly-report

Design card: https://claude.ai/artifact/LosWFBAWCCABJKeeNTHji3

Four boards, demo data from `seed_demo_data` after T4 (the 14 reviews 0, 20, 40, 60 and 80 days back), seeded and opened on Thursday Nov 5, 2026 (Vietnam time):

1. **Normal:** `/reports/`, November 2026 by default: Airport 1 review, 2.0, good 0, bad 1, "0.0" vs October; Downtown 1, 5.0, 1, 0, "▲ 1.0"; Riverside 1, 4.0, 1, 0, "▼ 1.0". "Reports" active in the sidebar, the "Month" select and "Show", the "Export CSV" button.
2. **Empty and wrong input:** July 2026, every location with "—" and 0 and "No reviews in July 2026."; "No locations yet" when there is no location; a wrong or too old `month` shows the current month.
3. **Narrow screen:** 360px, the sidebar on top, the table scrolls inside its panel, the page does not scroll sideways.
4. **CSV and rules:** `reviewradar-report-2026-09.csv` with its four lines, and the rules for month, average, good/bad, change and order.

The build must use the texts on the card (they are also in `specs/monthly-report/spec.md`) and the app's own colours from `app.css`, in light and dark. The dashed pink outline only marks what is new.
