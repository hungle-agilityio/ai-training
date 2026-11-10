# Spec: score-goals

## Summary

A location (Branch) gets an optional goal: a target score from 1.0 to 5.0 with one decimal. Signed-in users set the goals in a new "Location goals" panel on `/settings/`, which posts to its own URL `/settings/goals/`. The dashboard's Location scores table gets a "Goal" column, and the location page gets a "Goal" panel. A location meets its goal when its score (the rule of `average_from_totals`) is at least the goal. One migration adds a nullable field; the monthly report, Compare page, CSV exports and dashboard API do not change.

## Acceptance criteria

**The rule (T1)**

- **AC1.** `reviews/goals.py` has one rule, `goal_status(score, goal)`, that returns a frozen dataclass `GoalStatus` with `goal`, `met` (bool or None), `short_by` (Decimal or None) and `label` (str). Score is `float | None` (the location score), goal is `Decimal | None`.
- **AC2.** No goal: `label` is `–` (en dash), `met` and `short_by` are None, whatever the score.
- **AC3.** A goal and no score (no reviews): `label` is `No score yet`, `met` and `short_by` are None.
- **AC4.** Score at least the goal: `met` is True, `short_by` is None, `label` is `Met` (4.0 with goal 4.0 is Met).
- **AC5.** Score below the goal: `met` is False, `short_by` is goal minus score computed with Decimal to one decimal (goal 4.5, score 4.0 gives `Decimal("0.5")`; goal 3.0, score 2.0 gives `Decimal("1.0")`; no float error such as 0.49999), `label` is `0.5 short`.

**Storing goals (T2)**

- **AC6.** `Branch` gets `target_score`, a `DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)`, added by migration `0005_branch_target_score`. Existing locations get no goal.
- **AC7.** `reviews/goal_repository.py` reads the goals of all locations of the business, ordered by name then id, in one query, and saves a set of goals (location id → Decimal or None) in one transaction, updating only the locations whose goal changed.
- **AC8.** `seed_demo_data` sets demo goals: Downtown 4.5, Riverside 3.0, Airport none. Extra locations (`--branches`, `--with-new-branch`) get none. Everything else the seed does is unchanged.

**Setting goals on Settings (T3)**

- **AC9.** `/settings/` shows a panel `<section class="panel settings-panel" id="settings-goals">` titled "Location goals", below the Account panel and above Reply suggestions, with the help text "Target score from 1.0 to 5.0. Leave empty for no goal." and one number field per location (label = location name, `step="0.1"`, `min="1.0"`, `max="5.0"`, name `goal-<location id>`), in the order of AC7, and one button "Save goals". With no locations it shows "No locations yet." and no button.
- **AC10.** The form posts to `/settings/goals/` (POST only; GET redirects to `/settings/`). A valid post saves the goals and redirects to `/settings/?goals=saved`, where the notice "Goals saved." (`id="goals-saved"`, `role="status"`) shows once; an empty field clears the goal.
- **AC11.** A value below 1.0, above 5.0, with more than one decimal or not a number is refused: nothing is saved, the page shows `/settings/` again with each wrong field kept and the error "Enter a score from 1.0 to 5.0 with one decimal." under it, linked by `aria-describedby`. An unknown `goal-<id>` is ignored.
- **AC12.** The password form keeps working exactly as today at `/settings/`; a visitor who is not signed in is sent to sign in for `/settings/goals/`.

**Dashboard (T4)**

- **AC13.** The Location scores table on `/dashboard/` gets a column header "Goal" right after "Rating" (so the last three headers stay Status, Replied in 24h, Details). Each cell shows the goal to one decimal and the label of AC2 to AC5 separated by ` · `, for example `4.5 · 0.5 short`, `3.0 · Met`, only `–` (muted) when there is no goal, `4.0 · No score yet` for a location with no reviews. Met uses `badge-positive`, short uses `badge-watch`.
- **AC14.** The dashboard still runs 3 queries, whatever the number of locations.

**Location page (T5)**

- **AC15.** `/locations/<id>/` shows a panel `<section class="panel" id="location-goal">` titled "Goal" right after the Score panel: "Target 4.5", then the label (Met / 0.5 short / No score yet) with the same badges as AC13, and a link "Change goal" to `/settings/#settings-goals`. With no goal it shows "No goal set." and the link "Set a goal".
- **AC16.** The location page runs at most one query more than today.

**All tasks**

- **AC17.** Every test on `main` passes unchanged; `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` pass. Each task puts its tests in the new test files it names.

## Edge cases

- Empty: no locations → Settings panel says "No locations yet."; the dashboard empty state is unchanged.
- Large data: 50 locations → 50 fields on Settings; the dashboard still uses 3 queries.
- Permissions: every signed-in user can set goals; visitors are sent to sign in.
- A location with a goal and no reviews shows "No score yet", never "Met" or "short".

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Who sets goals | Any signed-in user | Superuser only | The app has no roles |
| Q2 Goal value | 1.0 to 5.0, one decimal, empty = no goal | Whole numbers | Same precision as the score |
| Q3 Met rule | Score ≥ goal = Met, else "x.x short"; no reviews = No score yet | Within 0.1 counts as met | Plain and exact |
| Q4 Where set | Settings panel, own URL `/settings/goals/` | On each location page | One place; the password form stays untouched |
| Q5 Dashboard | "Goal" column after Rating, still 3 queries | Badge only | The number matters to the owner |
| Q6 Location page | "Goal" panel after Score | Nothing | The page staff open most |
| Q7 History | Only the current goal | A log | Smaller; can come later |
| Q8 Scope | Reports, Compare, CSV, API unchanged | Also the monthly report | Keeps the epic at 5 tasks |

## Design

Design card linked in `design/score-goals/README.md` (https://claude.ai/artifact/FSwU4PMGBffS4rFt6KxMy6).

## Open questions
