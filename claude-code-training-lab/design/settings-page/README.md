# Design: settings-page

Design card: https://claude.ai/artifact/7hEB5npDfnU5QP7KEytCvd

Five boards on `/settings/` (demo data from `seed_demo_data`: user `demo`):

1. **Normal:** "Settings" active in the sidebar; the Account panel (username, "Change password" form with three fields, the hint and the button) and the Reply suggestions panel with "On" and "Model: claude-haiku-5-5" (AC1 to AC4, AC11, AC12).
2. **Saved:** `/settings/?saved=1` with the green line "Password changed." (AC5).
3. **Error:** Django's messages under the fields for a wrong current password and two passwords that differ; the fields come back empty (AC6).
4. **Demo and Off:** the Reply suggestions panel in demo mode (DEBUG on, no key) and off (no key on the live site); no model line, never the key (AC11, AC12).
5. **Narrow:** at 360px the panels stack, fields take the full width, no sideways scroll (AC9).

The build must use the texts on the card (they are also in `specs/settings-page/spec.md`) and the app's own colours from `app.css`, in light and dark. The dashed pink outline only marks what is new.
