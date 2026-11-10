# Spec: reply-templates

## Summary

A new table `ReplyTemplate` (name, text, kind) holds reply templates shared by the whole app. A pure rule in `reviews/reply_templates.py` checks a template and fills `{location}`. The Settings page gets a "Reply templates" panel that lists the templates and adds one; each template has its own edit page with a Delete step. The reply page of a review gets a "Template" select and a "Use template" button that fills the reply box without saving. `seed_demo_data` adds three demo templates. One migration adds the table; saved replies, the Reply drafts page, the Reviews page, the reports and the API do not change.

## Acceptance criteria

**The rule (T1)**

- **AC1.** `reviews/reply_templates.py` defines the kinds `good`, `bad` and `any` with the labels "Good review (4–5 ★)", "Bad review (1–2 ★)" and "Any review", and `kinds_for_rating(rating)`: 4 and 5 give `good` and `any`; 1 and 2 give `bad` and `any`; 3 gives only `any`. The good and bad ranges come from `RATING_RANGES`.
- **AC2.** `fill_template(text, location_name)` replaces every `{location}` with the location name and returns the result; a text without placeholders is returned unchanged. A location name that itself contains `{location}` is not replaced again.
- **AC3.** `template_errors(name, text)` returns a list of error messages, empty when the template is valid: name stripped must be 1 to 60 characters ("Enter a name of 1 to 60 characters."); text stripped must be 1 to 1,000 characters ("Write a text of 1 to 1,000 characters."); every `{word}` in the text other than `{location}` is refused ("Unknown placeholder {word}. You can use {location}.", one message per distinct unknown placeholder, in order of first appearance). A lone `{` or `}` is allowed.
- **AC4.** The rule has no database access and no Django model import.

**Storing templates (T2)**

- **AC5.** Model `ReplyTemplate` with `name` (CharField 60), `text` (TextField), `kind` (CharField 4, choices `good`, `bad`, `any`), `created_at`, `updated_at`; added by migration `0006_replytemplate`. No change to `Review`, `Branch` or `ReviewReply`.
- **AC6.** `reviews/template_repository.py`, the only place that queries templates: list all templates ordered by name (case-insensitive) then id, in one query; list the templates of given kinds in the same order, in one query; get one by id (None when missing); create; update name, text and kind; delete one; tell whether another template already has a name (ignoring case, excluding a given id).
- **AC7.** `seed_demo_data` deletes all templates and adds three:
  - "Thank you", good: "Thank you for your kind words! The team at {location} is glad you had a good visit, and we hope to see you again soon."
  - "We are sorry", bad: "We are sorry your visit to {location} did not go well. Please contact us so we can make it right."
  - "Thanks for the feedback", any: "Thank you for taking the time to share your feedback about {location}. It helps us improve."
  Everything else the seed does is unchanged.

**Settings panel (T3)**

- **AC8.** `/settings/` shows `<section class="panel settings-panel" id="settings-templates">` titled "Reply templates", after Location goals and before Reply suggestions, with the help text "Use {location} for the location's name." It lists each template in the order of AC6 as one row: the name, the kind label of AC1 and a link "Edit" to `/settings/templates/<id>/`. With no templates it shows "No reply templates yet." Below the list, an "Add a template" form: Name (text, maxlength 60), Kind (select, Any review first, then Good, then Bad), Text (textarea, maxlength 1000) and a button "Add template".
- **AC9.** The form posts to `/settings/templates/` (POST only; GET redirects to `/settings/`). A valid post creates the template with the stripped name and text and redirects to `/settings/?templates=added#settings-templates`, where the notice "Template added." (`id="templates-saved"`, `role="status"`) shows.
- **AC10.** An invalid post (AC3 errors, an unknown kind, or a name another template already has: "A template with this name already exists.") saves nothing and shows `/settings/` again with the typed values kept and each error under its field, linked by `aria-describedby`; the other panels show as on a normal visit.
- **AC11.** `/settings/` runs at most 4 queries (3 on `main`).

**Edit and delete (T4)**

- **AC12.** `/settings/templates/<id>/` (GET and POST) shows "Edit reply template" with the form of AC8 filled with the template, a button "Save template", a link "Cancel" to `/settings/#settings-templates` and a link "Delete template" to `/settings/templates/<id>/delete/`. An unknown id is 404.
- **AC13.** A valid post saves the change and redirects to `/settings/?templates=saved#settings-templates` with the notice "Template saved."; an invalid post follows AC10 (its own name does not count as taken) and shows the edit page again.
- **AC14.** `/settings/templates/<id>/delete/` GET shows "Delete the template "<name>"? Saved replies do not change." with a button "Delete template" (POST) and a link "Cancel" back to the edit page. The POST deletes the template and redirects to `/settings/?templates=deleted#settings-templates` with the notice "Template deleted." Saved replies never change. An unknown id is 404.
- **AC15.** The edit page and the delete page each run at most 3 queries.

**Reply page (T5)**

- **AC16.** The reply page `/reviews/<id>/reply/` shows, above the reply box, a `<div class="reply-template" id="reply-template">` with a select "Template" (name `template`) listing the templates of the kinds for the review's rating (AC1) in the order of AC6, and a button "Use template" (`name="action" value="template"`, `formnovalidate`).
- **AC17.** Pressing "Use template" replaces the text in the box with the chosen template filled with the review's location name (AC2), shows "Template filled in. Edit it before you save." (`role="status"`) and saves nothing. An unknown template id, or one whose kind does not fit the rating, keeps the typed text and shows "Choose a template from the list."
- **AC18.** With no fitting templates, the select and button are not shown; the page shows "No reply templates yet. Add them in Settings." with a link to `/settings/#settings-templates`.
- **AC19.** The reply page GET runs at most 2 queries (1 on `main`); a "Use template" post at most 3; "Suggest a reply" at most 3 (2 on `main`); saving a reply is unchanged.
- **AC20.** "Save reply" and "Suggest a reply" work as today.

**All tasks**

- **AC21.** `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` pass. Each task puts its new tests in the new test files it names; existing tests change only where its issue lists them under "Existing tests that change".

## Edge cases

- Empty: no templates → Settings says "No reply templates yet."; the reply page shows the line of AC18.
- A 3-star review sees only "Any review" templates.
- A location name with characters like `&` or `<` is escaped on the page as any other text.
- A template deleted while a reply page is open: "Use template" shows "Choose a template from the list."
- Large data: 50 templates → one query for the list on each page.
- Permissions: every signed-in user; visitors are sent to sign in for every new URL.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Who manages templates | Any signed-in user | Staff only | The app has no roles |
| Q2 Fields | Name, text, kind (good / bad / any) | Name and text only | Kind puts the right templates on each review |
| Q3 Placeholders | Only `{location}`; unknown ones refused | Also `{rating}`; none | The only value always known; no customer name stored |
| Q4 Owner of the list | One shared list | One per location | One business per installation |
| Q5 Use on reply page | Select + "Use template" post, no JavaScript | JavaScript insert | Same pattern as "Suggest a reply" |
| Q6 Which templates show | Kinds that fit the rating + Any | All templates | Fewer wrong choices |
| Q7 Empty state | Line with a link to Settings | Nothing | Tells staff the feature exists |
| Q8 Edit and delete | Edit page, delete with a confirm step | Add only | A typo must be fixable |
| Q9 Record template on reply | No | Template link on each reply | No second migration |
| Q10 Demo templates | Three (good, bad, any) | None | The demo shows the feature |
| Q11 Query budget | Reply page +1, Settings +1 | Load on click | One list query per page |

## Design

Design card linked in `design/reply-templates/README.md` (https://claude.ai/artifact/LxZezTSrag9Rc3A1sDRgYS).

## Open questions
