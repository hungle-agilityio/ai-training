# Domain

ReviewRadar is an online reputation tool for businesses with several branches (clinics, spas, salons). It collects customer reviews, shows a score per branch, and later classifies sentiment and suggests replies.

- **Branch** (called "location" in tickets): one place of a business. **Review**: a customer review with rating 1 to 5, text, date.
- **Score of a branch:** average rating to one decimal, rounded half up; no reviews means no score (not 0). One rule in `reviews/services.py` (`average_from_totals`).
- **Week:** Monday to Sunday in Vietnam time.
- **Good / bad review:** good is rating 4 to 5, bad is 1 to 2 (`RATING_RANGES`).
- Audience of tickets: QA, BA and clients, in plain language.

Full background, MVP scope and planned entities: `docs/app/reviewradar-project-context-2026-10.md`. Rules found later go to `knowledge/BUSINESS_RULES.md`.
