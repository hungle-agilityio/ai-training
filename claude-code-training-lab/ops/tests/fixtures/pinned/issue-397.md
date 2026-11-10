## Summary

Settings gets a "Location goals" panel where any signed-in user sets or clears the target score of each location.

Part of the epic #394
Depends on #396
Spec: https://github.com/hungle-agilityio/ai-training/blob/main/claude-code-training-lab/specs/score-goals/spec.md (AC9 to AC12, AC17)
Design card: https://claude.ai/artifact/FSwU4PMGBffS4rFt6KxMy6

## Done when

- **AC1.** `/settings/` shows `<section class="panel settings-panel" id="settings-goals">` titled "Location goals", below Account and above Reply suggestions, with the help text "Target score from 1.0 to 5.0. Leave empty for no goal." and one number field per location (label = location name, `step="0.1"`, `min="1.0"`, `max="5.0"`, name `goal-<location id>`), ordered by name then id, and one button "Save goals". With no locations it shows "No locations yet." and no button.
- **AC2.** The form posts to `/settings/goals/` (POST only; GET redirects to `/settings/`). A valid post saves the goals and redirects to `/settings/?goals=saved`, where "Goals saved." (`id="goals-saved"`, `role="status"`) shows once; an empty field clears the goal.
- **AC3.** A value below 1.0, above 5.0, with more than one decimal or not a number is refused: nothing is saved, `/settings/` shows again with each wrong field kept and "Enter a score from 1.0 to 5.0 with one decimal." under it, linked by `aria-describedby`. An unknown `goal-<id>` is ignored.
- **AC4.** The password form works exactly as today; a visitor who is not signed in is sent to sign in for `/settings/goals/`.
- **AC5.** Every test on `main` passes unchanged; ruff, mypy and pytest pass. New tests go in `reviews/tests/integration/test_settings_goals.py`.

## Screens to capture

```json
{"steps": [{"name": "settings-goals", "goto": "/settings/", "capture": "#settings-goals"}]}
```

## Files likely touched

- `reviews/goal_forms.py` (NEW)
- `reviews/goal_views.py` (NEW)
- `reviews/views.py`
- `reviewradar/urls.py`
- `reviews/templates/reviews/settings.html`
- `reviews/static/reviews/settings.css`
- `reviews/tests/integration/test_settings_goals.py` (NEW)
