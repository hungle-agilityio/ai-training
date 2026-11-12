# Spec: app-prototype

## Summary

The spec pull request adds `design/app/prototype.html`: every screen of ReviewRadar in one self-contained, clickable file on the demo data of `seed_demo_data`, with actions and animations, and 33 named states that open directly with `#<state>`. It is published as the private Artifact https://claude.ai/artifact/C1yKaZyCxYEex5qhXQFuoE. Then four tasks: the verify report shows "Design vs build" (T1), the spec templates name prototype states instead of a design card (T2), ADR-030 and the Project rules add the Prototype step (T3, by hand), and the dashboard stops overflowing at phone width, as the prototype shows (T4).

## User story

As the owner, I want one prototype of the whole app that I can click through before the work is split, so that I approve what users will see before anyone builds it.

As the owner, I want each build's verify report to put the designed screen next to the built one, so that I see any difference without opening the app.

As a ReviewRadar user on a phone, I want the dashboard to fit my screen, so that I do not scroll sideways to read it.

## Acceptance criteria

**The prototype (this spec pull request)**

- **AC1.** `design/app/prototype.html` is one file with no network request. It shows every screen of the app on `main` 5213e39: Sign in, Dashboard, Reviews, Import reviews, Reply drafts, Reply to a review (with Follow-up), Location, Monthly report, Topics, Compare locations, Settings (Account, Locations, Location goals, Reply templates, Reply suggestions), Rename location, Edit reply template, Delete reply template (as a dialog) and Page not found. Its data is that of `seed_demo_data`: Airport, Downtown and Riverside, 14 reviews, 3 reply templates, goals 4.5 (Downtown) and 3.0 (Riverside).
- **AC2.** Given the prototype opened at `#dashboard`, when the owner looks at the numbers, then they equal the app's on the same data: Locations 3, Total reviews 14, Average rating 3.2, Need attention 1, Need a reply 5 (1 overdue), Replied in 24h 50% (2 of 4 bad reviews, average 17.7 h), Open cases 3.
- **AC3.** Every action works in the page, with the app's texts: sign in (password `demo`), sign out, filter and search reviews, pagination, reply with a template or a suggestion and save, save a follow-up, import a CSV (a chosen file, a dropped file or the sample), the four Settings forms with their errors, rename a location, edit and delete a template, compare two locations, change the report month and the topic filters. Downloads show the file's content in a dialog. Feedback is animated: page change, toasts, dialogs, loading states, bars that grow.
- **AC4.** Opening `prototype.html#<state>` shows that state directly, for each of the 33 ids in its `SCENARIOS` list (for example `dashboard`, `dashboard-empty`, `reviews-no-match`, `reply-suggest-failed`, `settings-goal-error`). With `?bare` the prototype bar is hidden, so a screenshot shows only the app. Without it, the bar lists the states and switches demo or empty data, working or failing outside services, and full or 390 px width.
- **AC5.** `design/app/README.md` links the Artifact, lists the 33 state ids, says how a thread updates the file and the Artifact together, and lists the one known difference from `main` (the phone-width fix of T4). `design/README.md` says the app prototype is the design for every screen, that `design/<feature>/` folders are history, and no longer says that `capture-before-after` compares the built screens with the design.

**Design vs build in the verify report (T1)**

- **AC6.** A step of an issue's `## Screens to capture` block may carry `"design": "<state id>"`. `check-in-browser` keeps ignoring unknown keys (no change there).
- **AC7.** Given a needs-ui issue whose block has the step `{"name": "dashboard", "goto": "/dashboard/", "capture": "#location-scores", "design": "dashboard"}`, when `build_report.py --browser --spec <file>` runs, then `report.html` has a section `Design vs build` with one row: the screenshot of `design/app/prototype.html?bare#dashboard` taken at the same window size as the build's screenshot of that step (1280 by 800 unless the spec sets `viewport`), on the left, captioned `Design: dashboard`, and the build's screenshot on the right, captioned `Build: dashboard`.
- **AC8.** `report.json` gets `"design_pairs"`: one entry per step with `"design"`, in step order, each with `"step"`, `"state"`, `"design_screenshot"` (a file name in the report folder, or `null`), `"build_screenshot"` and `"note"` (`""` or the reason). Without any `"design"` step the key is `[]` and `report.html` has no such section.
- **AC9.** When the prototype file is missing, or the state id is not in its `SCENARIOS` list, the row shows `Design not found: <state id>` with the build screenshot alone, and `"note"` says the same. The report is still written, and no verdict, axis or exit code changes because of a design row.
- **AC10.** The comparison never fails a build: no pixel difference is computed and no status depends on it (Q5).
- **AC11.** `build_report.py --design PATH` sets the prototype file; the default is `design/app/prototype.html` in the folder the report runs from. The design screenshots are taken with Playwright directly from the file, with no server and no sign-in.
- **AC12.** `work-queue` and `write-issue` say: a step's `"design"` names the prototype state the build must match; the verify report shows each design next to the built screen; a difference is reported, never fixed by changing the prototype. The sentence that `capture-before-after` compares the real screens with the design is removed.
- **AC13.** Plugin version: one patch number above the version on the task's base branch (`ops/check_plugin_version.py`). New tests in `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py`; every test on `main` passes unchanged.

**Spec templates (T2)**

- **AC14.** `docs/app/templates/spec/spec.md`, section `## Design`: the placeholder becomes `<the prototype states this feature adds or changes, as #<state> ids of design/app/prototype.html, approved with "Prototype ổn"; or "nothing visible to users">`.
- **AC15.** `docs/app/templates/spec/tasks.md`: the example of `## Screens to capture` gains `"design": "<state id>"` on its step, and the comment says that every step whose page has a prototype state names it.

**ADR-030 and the Project rules (T3, by hand)**

- **AC16.** `.claude/knowledge/decisions/ADR-030-app-prototype.md` records the decision (Q1 to Q6, the decisions table below) and its date, 2026-11-12. `.claude/knowledge/decisions/README.md` lists it.
- **AC17.** `.claude/project-instructions.md`: a Prototype step between Grill-me and Spec. When users will see a change (either lane), a thread updates `design/app/prototype.html` (new screens and states as `SCENARIOS` ids, demo data, real actions and animations), republishes the same Artifact so the link stays, and posts a card "Prototype ổn / Sửa". Epics and tasks are split only after "Prototype ổn". Full lane: the spec pull request carries the prototype change. Fast lane: "Prototype ổn" is also the OK of Gate 1, and the thread opens a pull request `design: <feature>` that changes only `design/app/prototype.html` and merges it on that same press. The design card of step 3 and the Definition of Ready line "a design card when users see a change" are replaced by "the prototype shows every screen and state the task changes, approved with Prototype ổn, and its `## Screens to capture` steps name those states with `design`".
- **AC18.** `.claude/CLAUDE.md`, "Removed, and why": one row for 2026-11-12, "One design card per feature", why "the owner wants the whole app designed and clickable before the work is split", rebuild from "ADR-030, `design/<feature>/`". The owner pastes the new Project instructions into Project settings; the thread gives the text as a file.

**Dashboard at phone width (T4)**

- **AC19.** Given the dashboard of the demo data, when it is shown 390 px wide, then the page is not wider than the screen (`document.documentElement.scrollWidth` is 390) and the "Location scores" table scrolls inside its panel, as in the prototype state `dashboard` at 390 px.
- **AC20.** Given the same dashboard 1280 px wide, then the layout is unchanged: the two panels of the grid keep their widths.
- **AC21.** New tests in `reviews/tests/integration/test_dashboard_narrow.py` (the CSS rule that lets grid panels shrink is served in `app.css`) and the browser check of the issue; every test on `main` passes unchanged.

## Edge cases

- Empty: the prototype has `dashboard-empty`, `reviews-empty`, `replies-empty`, `settings-empty`; T1 with no `"design"` step adds nothing to the report.
- Large data: the prototype paginates at 20 reviews like the app; imports of many rows paginate the same way.
- Permissions: the prototype is a private Artifact; only the owner can share it. The file holds demo data only, never customer data.
- Errors: failing outside services (suggestion, import) are a switch in the prototype bar and named states.
- A state removed from the prototype later: the build's row says `Design not found` and the owner decides.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Form of the prototype | One HTML file `design/app/prototype.html`, published as a private Artifact | Artifact only | Versioned with the spec, and the loop can open it |
| Q2 Prototype or design card | The prototype replaces the design card | Keep both | One thing to review |
| Q3 What it covers | The whole app, every screen and state; every needs-ui request updates it first, fast lane too | One prototype per epic | One source of truth for the UI (owner: design the whole app first, then split epics and tasks) |
| Q4 Where the owner approves | A card "Prototype ổn / Sửa" before the split into epics and tasks; "Merge PR spec" stays Gate 1 | Only at "Merge PR spec" | The owner tries the flow before the work is split |
| Q5 Compare design and build | Side by side in the verify report, no automatic failure | Pixel diff that fails the build; no compare | Demo CSS and app CSS differ in small ways; the owner judges |
| Q6 First version | Built now from the screens on `main`, in this spec pull request | Rules only | The step has a real source of truth from day one |
| Actions | Real actions and animations on demo data, no backend | Static screens | Owner: "prototype có action và animation như thật" |
| Fast lane with a visible change | "Prototype ổn" is the Gate 1 OK; a `design:` pull request with only the prototype, merged on that press | Send every visible change to the full lane | Keeps small UI work light (owner prefers a simple flow) |
| Dashboard overflow found while building the prototype | Fixed in the prototype; built as T4 | Copy the bug into the prototype | The prototype shows the target, the build matches it |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

The whole app: `design/app/prototype.html`, Artifact https://claude.ai/artifact/C1yKaZyCxYEex5qhXQFuoE, approved with "Prototype ổn" on 2026-11-12. T4 matches state `dashboard` at 390 px.

## Open questions
