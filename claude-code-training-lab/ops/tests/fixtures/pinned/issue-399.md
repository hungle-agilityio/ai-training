## Summary

The location page gets a "Goal" panel next to Score: the target, whether it is met or how far short, and a link to change it.

Part of the epic #394
Depends on #395
Depends on #397
Spec: https://github.com/hungle-agilityio/ai-training/blob/main/claude-code-training-lab/specs/score-goals/spec.md (AC15 to AC17)
Design card: https://claude.ai/artifact/FSwU4PMGBffS4rFt6KxMy6

## Done when

- **AC1.** `/locations/<id>/` shows `<section class="panel" id="location-goal">` titled "Goal" right after the Score panel: "Target 4.5", then the label (Met / 0.5 short / No score yet) with `badge-positive` for Met and `badge-watch` for short, and a link "Change goal" to `/settings/#settings-goals`. With no goal it shows "No goal set." and the link "Set a goal".
- **AC2.** The location page runs at most one query more than on `main`.
- **AC3.** Every test on `main` passes unchanged; ruff, mypy and pytest pass. New tests go in `reviews/tests/integration/test_location_goal.py`.

## Screens to capture

```json
{"steps": [{"name": "location-goal", "goto": "/locations/2/", "capture": "#location-goal"}]}
```

## Files likely touched

- `reviews/views.py`
- `reviews/templates/reviews/location.html`
- `reviews/static/reviews/app.css`
- `reviews/tests/integration/test_location_goal.py` (NEW)
