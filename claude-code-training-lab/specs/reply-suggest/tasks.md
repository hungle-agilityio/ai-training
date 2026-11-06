# Tasks: reply-suggest

Three tasks. T2 builds on T1. T3 only writes two rules into `.claude/knowledge/BUSINESS_RULES.md`, which the loop may not edit, so it is built by hand; it shares no file with T1 or T2 and can run any time. No task needs a new package: the app calls the Claude API with the Python standard library (Q2), so `pyproject.toml` and `uv.lock` do not change.

## T1: Reply suggestion service

- **ACs:** AC1 to AC10
- **Files likely touched:** `reviewradar/settings.py`, `reviews/claude_client.py` (NEW), `reviews/reply_suggestion.py` (NEW), `../render.yaml`, `reviews/tests/unit/test_reply_suggestion.py` (NEW), `reviews/tests/unit/test_claude_client.py` (NEW), `reviews/tests/integration/test_render_blueprint_claude_key.py` (NEW)
- **Depends on:** none
- **Risk:** high (external service, a secret, personal data sent outside)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:app`

## T2: "Suggest a reply" button on the reply page

- **ACs:** AC11 to AC17
- **Files likely touched:** `reviews/views.py`, `reviews/forms.py`, `reviews/templates/reviews/reply.html`, `reviews/static/reviews/replies.css`, `reviews/tests/integration/test_reply_suggest_page.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (user input, an external call from a page)
- **needs-ui:** yes
- **Screens to capture:** `/reviews/1/reply/` (the first demo review, Airport, 2 stars, on a fresh demo database, DEBUG on, so the fake suggestion is used) → `#reply-form`; the same page after a click on `#suggest-reply` → `#reply-form`
- **Label:** `agent:ready`, `area:app`

## T3: Record the reply suggestion rules

- **ACs:** AC18
- **Files likely touched:** `.claude/knowledge/BUSINESS_RULES.md`
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual`, `area:app`

AC19 is checked by the owner after the release.
