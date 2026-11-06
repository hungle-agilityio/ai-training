# Spec: reply-suggest

## Summary

The reply page `/reviews/<id>/reply/` (epic #236) gets a "Suggest a reply" button. It sends the review's text, rating and location name to the Claude API and puts the answer in the reply box, in the language of the review and signed "— <location> team". The manager edits it and presses "Save reply" as today; nothing is saved before that. The app calls the API with the Python standard library, so no package is added. Without an API key the button is hidden, except in local runs with DEBUG on, where a fixed demo draft is used so no key and no money are needed. Tests never reach the network. No model, no migration, no new page. The live site changes at the next release, after the owner has put `ANTHROPIC_API_KEY` on Render (ADR-017).

## Acceptance criteria

Suggestion service (T1):

- **AC1.** `reviewradar/settings.py` reads three values from the environment: `ANTHROPIC_API_KEY` (trimmed, default `""`), `ANTHROPIC_MODEL` (trimmed, default `"claude-haiku-5-5"` when missing or empty) and `REVIEWRADAR_AI_FAKE` (True only for the value `"1"`). The key is never printed, logged, put in a page or in an error message.
- **AC2.** A new module `reviews/reply_suggestion.py` has `suggestion_mode() -> Literal["off", "fake", "live"]`: `"fake"` when `REVIEWRADAR_AI_FAKE` is True, or when `DEBUG` is on and the key is empty; otherwise `"live"` when the key is set; otherwise `"off"`.
- **AC3.** A new module `reviews/claude_client.py` is the only code that talks to the Claude API. `create_message(*, api_key: str, model: str, system: str, user_text: str, max_tokens: int, timeout: float) -> str` sends one `POST` to `https://api.anthropic.com/v1/messages` with `urllib.request`, the headers `x-api-key`, `anthropic-version: 2023-06-01` and `content-type: application/json`, and the JSON body `{"model", "max_tokens", "system", "messages": [{"role": "user", "content": user_text}]}` and nothing else. It returns the text of the `text` blocks of the answer, joined. On an HTTP error, a network error, a timeout, an answer that is not JSON or an answer with no text it raises `ClaudeError` (one class defined in the module), whose message holds only the error kind and the HTTP status, never the key or the texts.
- **AC4.** `reply_suggestion` has the constants `SUGGESTION_TIMEOUT_SECONDS = 15`, `SUGGESTION_MAX_TOKENS = 500` and `REPLY_SYSTEM_PROMPT`. The prompt tells Claude to: write in the same language as the review; be polite and short, at most 600 characters, plain text; for a rating of 1 or 2 apologise, name the problem from the review and invite the customer to contact the location; for 3 thank and answer the concern; for 4 or 5 thank; never promise a refund, a discount or any compensation; never add facts that are not in the review; write no signature and no placeholder such as `[Name]`.
- **AC5.** The user message is exactly four lines: `Location: <location name>`, `Rating: <n> out of 5`, `Review:`, then the review text. Nothing else is sent: no user name, no review id, no other review, no reply already saved.
- **AC6.** `suggest_reply(review_id: int) -> ReplySuggestion | None` reads the review and its location (one query; None for an unknown review) and returns the frozen dataclass `ReplySuggestion(status: Literal["ok", "failed", "off"], draft: str)`. `"off"`: mode off, no call, draft `""`. `"fake"` mode: status `"ok"`, the draft is `FAKE_REPLY_TEXT` ("Thank you for taking the time to share your experience. We are sorry it fell short of what you expected, and we would like to make it right. Please contact us so we can help.") plus the signature, and no network. `"live"` mode: one call to `create_message` with the settings model, `SUGGESTION_MAX_TOKENS` and `SUGGESTION_TIMEOUT_SECONDS`; a `ClaudeError` or an empty answer gives status `"failed"` and draft `""`, with no retry.
- **AC7.** The draft is the answer without spaces and line breaks at both ends, then a blank line, then the signature `— <location name> team` (for example `— Airport team`). When it would be longer than 1000 characters (`REPLY_MAX_LENGTH`), the answer is cut at the last space that keeps the whole draft at 1000 characters or fewer, so `clean_reply_text(draft)` never returns None.
- **AC8.** A failed suggestion writes one warning with the logger `reviews.reply_suggestion`: `Reply suggestion failed: <error kind> <HTTP status or ->`. No log line ever holds the key, the review text, the prompt or the draft.
- **AC9.** `render.yaml` at the repository root gets `- key: ANTHROPIC_API_KEY` with `sync: false` and no value; the other entries do not change.
- **AC10.** Tests in new files `reviews/tests/unit/test_claude_client.py`, `reviews/tests/unit/test_reply_suggestion.py` and `reviews/tests/integration/test_render_blueprint_claude_key.py` cover AC1 to AC9 with `urllib.request.urlopen` or `create_message` mocked (pytest-mock), never the network: the request URL, headers and body; each error kind; each mode; the four-line message; the signature; a 1200-character answer cut to 1000 or fewer; the log line without the review text.

Reply page (T2):

- **AC11.** When `suggestion_mode()` is `"fake"` or `"live"`, the reply form gets a second submit button after "Save reply": `<button type="submit" name="action" value="suggest" id="suggest-reply" formnovalidate>` with the text "Suggest a reply", styled as a secondary button (outline, not filled), and a line `id="suggest-hint"`: "Claude writes a draft in the box. Nothing is saved until you press Save reply." When the mode is `"off"` the page is exactly as today.
- **AC12.** A `POST` with `action=suggest` never saves. With status `"ok"` it answers 200 with the same page, the draft in `#reply-text`, and above the box the line "Suggested by Claude. Read and edit it before you save." (`role="status"`, class `suggest-note`). A reply already saved stays saved and its "Last saved" line stays.
- **AC13.** With status `"failed"` it answers 200 with the line "Could not get a suggestion right now. Try again or write your own." (class `alert`) and the text the manager had typed kept in the box. With status `"off"` it answers 200 with the typed text kept and no message. The "Write a reply of 1 to 1,000 characters." line is never shown after `action=suggest`.
- **AC14.** A `POST` with no `action` or any other value saves as today (AC18 and AC19 of `specs/review-replies/spec.md`; the existing tests stay green). An unknown review id answers 404. A `POST` without the CSRF token answers 403. `action` is read by a form in `reviews/forms.py`, not from `request.POST` in the view.
- **AC15.** Without sign-in checks a `POST` with `action=suggest` makes at most 2 queries and at most one call to the API; a `GET` makes no call. A visitor who is not signed in gets a 302 to the login page and no call is made.
- **AC16.** At 360px wide the two buttons wrap and the page does not scroll sideways. New styles go in `reviews/static/reviews/replies.css`.
- **AC17.** Tests in a new file `reviews/tests/integration/test_reply_suggest_page.py` cover AC11 to AC16 with `reply_suggestion.suggest_reply` or `create_message` mocked; the sign-in test is marked `login`.

Rules (T3):

- **AC18.** `.claude/knowledge/BUSINESS_RULES.md`, section "Confirmed", gets two rules: (1) a reply suggestion sends only the review text, its rating and the location name to Claude (Anthropic); never a staff name or other reviews; the review text and the draft are never written to the app's logs; (2) a suggestion is in the review's language, signed "— <location> team", at most 1000 characters, never promises a refund or compensation, and is saved only when staff press "Save reply".

After the release:

- **AC19.** Before the release the owner puts `ANTHROPIC_API_KEY` in the Render dashboard and sets a monthly spend limit in the Anthropic console. After the release (`ops/release.py`), signed in as `demo` on the live site, the owner opens the reply page of the Airport 2★ review "Waited 50 minutes, nobody apologized.", presses "Suggest a reply" and gets an English draft that ends with "— Airport team"; on the Riverside 2★ review "Nhân viên lễ tân chưa nhiệt tình" the draft is in Vietnamese. The owner edits one draft, saves it and sees "Reply saved.".

## Edge cases

- Empty: a review with an empty text still gets a suggestion from its rating; the four-line message keeps an empty last line.
- No key on the live site: the button is hidden (AC11), so nobody presses a button that cannot work.
- Slow or failing API: the page waits at most 15 seconds, then shows the error of AC13; what was typed is never lost.
- An answer longer than allowed is cut (AC7); a draft never fails the 1000-character rule when saved.
- The manager presses the button twice: each press is one new call and replaces the box with the new draft.
- Language: the reply follows the review's language; the signature stays "— <location> team" in every language (Q5).
- Permissions: sign-in is needed (AC15); every signed-in user may ask for a suggestion on any review, as with saving a reply.
- Personal data: only the review text, rating and location name leave the app (AC5); the box keeps `data-sensitive="reply-text"`.
- A machine that has `ANTHROPIC_API_KEY` in its environment and DEBUG on calls the real API; set `REVIEWRADAR_AI_FAKE=1` to avoid it.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 How the draft appears | A button posts the form; the page comes back with the draft in the box, not saved | JavaScript fills the box without a reload | Same pattern as the form today, works without JavaScript, easy to test |
| Q2 How the app calls Claude | Python standard library (`urllib`) | The `anthropic` package | The loop may not edit `pyproject.toml` or `uv.lock`; no extra manual task |
| Q3 Model | `claude-haiku-5-5`, changeable with `ANTHROPIC_MODEL` | `claude-sonnet-5-5` | Fast and cheap for a short reply; the model can change without code |
| Q4 Language and tone | The review's language; polite, short, no promises, no invented facts | Always English | Demo reviews are in English and Vietnamese; customers read their own language |
| Q5 Signature | "— <location> team", added by the code | No signature | The reply comes from a branch; the code adds it so it is always the same |
| Q6 Errors | No key: no button; error or 15 s: a message, typed text kept, no retry | Button always shown | Nobody presses a button that cannot work; nothing typed is lost |
| Q7 Tests and the loop | Tests mock the call; fake draft with `REVIEWRADAR_AI_FAKE=1` or DEBUG without a key | A real key in the loop | No cost and no secret on the Mac mini; the loop's browser check runs with DEBUG on, so it sees the button |
| Q8 Cost | One call per press, 500 tokens at most, nothing stored, a spend limit in the Anthropic console | A limit of 20 per user per hour | Only signed-in staff can press it; no table or migration needed |
| Q9 Personal data | Send only the review text, rating and location name; never log texts; rule in `BUSINESS_RULES.md` | Also mask phone numbers and e-mails | The least data that gives a good reply; masking can come later |
| Q10 Live site | `ANTHROPIC_API_KEY` in `render.yaml` with `sync: false`; the owner pastes it before the release | Feature off on the live site | The secret never enters the repository; the feature shows at the release |

## Design

Design card linked in `design/reply-suggest/README.md`.

## Open questions
