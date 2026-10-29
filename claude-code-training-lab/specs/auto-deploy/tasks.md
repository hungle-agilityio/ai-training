# Tasks: auto-deploy

## T1: Add gunicorn and whitenoise to the locked dependencies

- **ACs:** AC1
- **Files likely touched:** `pyproject.toml`, `uv.lock`
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual` (the loop may not edit `pyproject.toml` or `uv.lock`)

## T2: Production settings, WSGI entry and noindex

- **ACs:** AC2, AC3, AC4, AC5, AC6, AC7
- **Files likely touched:** `reviewradar/wsgi.py` (new), `reviewradar/settings.py`, `reviews/templates/reviews/base.html`, `.gitignore` (lab folder, `staticfiles/`), `reviews/tests/integration/test_production_settings.py` (new)
- **Depends on:** T1, #61 (both change `settings.py`; #61 sets the three local hosts and its test checks them)
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`

## T3: Render Blueprint and Deploy section

- **ACs:** AC8, AC9, AC10, AC11 (AC12 to AC14 are checked by the owner after the one-time setup)
- **Files likely touched:** `render.yaml` (new, repository root), `claude-code-training-lab/README.md`, `claude-code-training-lab/reviews/tests/integration/test_render_blueprint.py` (new: reads `render.yaml` as text, since PyYAML is not a dependency, and checks the values of AC8 to AC10)
- **Depends on:** T2
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`
