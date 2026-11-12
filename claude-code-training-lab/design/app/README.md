# Design: the whole app

The prototype of every ReviewRadar screen, clickable on the demo data of `seed_demo_data` (Airport, Downtown, Riverside; 14 reviews). It is the design for every screen (ADR-030). Approved by the owner with "Prototype ổn" on 2026-11-12.

- File: [`prototype.html`](prototype.html), one self-contained page, no network request.
- Artifact (private): https://claude.ai/artifact/C1yKaZyCxYEex5qhXQFuoE

## Open a state

`prototype.html#<state>` opens a state directly; `prototype.html?bare#<state>` hides the prototype bar, for screenshots. The bar (button "Prototype") lists the states and switches demo or empty data, working or failing outside services (suggestion, import), and full or 390 px width. Sign in with any username and the password `demo`.

A needs-ui issue names the state its build must match with `"design": "<state>"` on a step of `## Screens to capture`; the verify report shows the two side by side.

| State (33) |
|---|
| `#login` |
| `#login-error` |
| `#dashboard` |
| `#dashboard-empty` |
| `#reviews` |
| `#reviews-filtered` |
| `#reviews-no-match` |
| `#reviews-search-short` |
| `#reviews-empty` |
| `#import` |
| `#import-done` |
| `#import-error` |
| `#replies` |
| `#replies-overdue` |
| `#replies-empty` |
| `#reply-1` |
| `#reply-error` |
| `#reply-suggest-failed` |
| `#reply-12` |
| `#location-1` |
| `#location-2` |
| `#reports` |
| `#topics` |
| `#compare` |
| `#compare-1-2` |
| `#compare-same` |
| `#settings-page` |
| `#settings-goal-error` |
| `#settings-location-error` |
| `#settings-empty` |
| `#rename-location-1` |
| `#edit-template-1` |
| `#not-found` |

## Update it

At the Prototype step a thread changes `prototype.html`: new screens and states go into `SCENARIOS`, data stays demo data, actions and animations work like the app. It republishes the same Artifact (same link) and asks the owner "Prototype ổn / Sửa". The file reaches `main` in the spec pull request (full lane) or in a `design:` pull request (fast lane). The CSS is the app's `app.css`, `replies.css` and `settings.css`, with `@media (max-width: …)` written as `@container app (max-width: …)` so the bar can switch to 390 px.

## Known differences from `main`

- Dashboard at phone width: panels of `.grid` may shrink (`.grid > * { min-width: 0; }`), so the Location scores table scrolls inside its panel. On `main` the page is 700 px wide at 390 px. Built by `specs/app-prototype` T4.
