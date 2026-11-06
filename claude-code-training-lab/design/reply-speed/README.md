# Design: reply-speed

Design card: https://claude.ai/artifact/G7ZR7nk6ktszYbhMog3kNH

Four boards on `/dashboard/` (demo data from `seed_demo_data` after T1):

1. **Normal:** a sixth KPI card "Replied in 24h" after "Need a reply": "50%", "2 of 4 bad reviews", "Average reply time 17.7 h"; cards 3 per row. A new column "Replied in 24h" in Location scores between Status and Details: Airport "0%", Downtown "–" (muted), Riverside "100%" (AC4, AC7, AC8).
2. **Empty:** "–" and "No bad reviews yet" (AC6).
3. **None replied, and days:** "0%", "0 of 2 bad reviews", "No replies yet"; and "33%", "1 of 3 bad reviews", "Average reply time 3.1 days" (AC5, AC6).
4. **Narrow:** at 360px the cards stay 2 per row (1 per row on very small screens), the table scrolls inside its box, no sideways page scroll (AC10).

The build uses the texts on the card (also in `specs/reply-speed/spec.md`) and the app's own colours from `app.css`, in light and dark. The new card is a plain card: no alert colour. The dashed pink outline only marks what is new.
