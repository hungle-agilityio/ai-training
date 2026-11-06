# Intent: reply-suggest

## Problem

Staff can now write a reply to each review (epic #236), but they start every reply from an empty box. Writing a calm, polite answer to an angry review takes time, so bad reviews wait. The MVP promised "Suggest a reply draft for each review" (`docs/app/reviewradar-project-context-2026-10.md`), and that is still missing.

## Goal

On the reply page of a review, a "Suggest a reply" button asks Claude for a short draft in the language of the review, signed with the location's name. The draft fills the reply box; the manager reads it, edits it and presses "Save reply" as today. Nothing is saved until they do. When Claude is not set up or does not answer, the page says so and the manager writes the reply by hand.

## Users

- Business staff and owners who are signed in, on `/reviews/<id>/reply/`. Every signed-in user may ask for a suggestion on any review, as with the reply itself.

## Out of scope

- Saving or listing suggestions (no `ReplyDraft` table, no migration), a history of suggestions, or several drafts to choose from.
- Posting the reply anywhere outside ReviewRadar.
- Sentiment classification, escalation rules, or reply templates.
- A limit per user or per hour; spending is limited in the Anthropic console instead.
- Masking phone numbers or e-mails in the review text before it is sent.
