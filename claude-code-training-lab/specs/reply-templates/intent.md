# Intent: reply-templates

## Problem

Staff write every reply from an empty box or ask Claude for a draft. Most replies say the same few things: thanks for a good visit, sorry for a bad one, thanks for the feedback. Typing them again each time is slow, and the wording differs from person to person. When Claude is off or has no key (as on the demo), staff have no help at all.

## Goal

The business keeps a short list of reply templates. Each has a name, a text and a kind (good review, bad review or any). The text may contain `{location}`, which becomes the location's name. Signed-in users add, edit and delete templates on the Settings page. On the reply page of a review, a "Template" select lists the templates that fit the review's rating; "Use template" fills the reply box with the filled-in text, which the user edits and saves as today.

## Users

The owner and staff of a business, signed in to ReviewRadar. Everyone who is signed in may manage templates and use them (the app has no roles).

## Out of scope

- Templates per location or per user; one shared list.
- Placeholders other than `{location}` (the customer's name is not stored).
- Recording which template a reply used, or counting uses.
- JavaScript on the reply page; the template is filled by a post, like "Suggest a reply".
- Templates on the Reply drafts page, the Reviews page, the reports or the dashboard API.
- Roles or permissions.
