# Spec: starter-refresh

## Summary

`ops/bootstrap.py --stack` copies every decision record the flow cites, writes an index of exactly the copied records, and moves the app prototype to `docs/design/prototype.html`, which the spec pull request of a new project may change. Then the template repository `agent-flow-starter` is refreshed from its output and the kickoff instructions get a Prototype step. Nothing visible to ReviewRadar's users.

## User story

As the owner, I want a new project made from the template to start with today's flow, so that I do not lose the work of ADR-026 to ADR-033 in every new project.

## Acceptance criteria

Bootstrap (loop task T1):

- **AC1.** `ops/bootstrap_manifest.toml` copies `.claude/knowledge/decisions/ADR-020-*.md` to `ADR-033-*.md` (one `[[copy]]` entry each, after ADR-019), so `bootstrap.py --stack python` into an empty clone writes `docs/decisions/ADR-008-*.md` to `ADR-033-*.md`: 26 files.
- **AC2.** In that output, every `ADR-NNN` cited by a `.md` file under `.claude/` or `.flow/plugin/` has its file in `docs/decisions/`.
- **AC3.** In that output, the `## Index` of `docs/decisions/README.md` links exactly the `ADR-*.md` files of `docs/decisions/` (no ADR-001 to ADR-007); the text above `## Index` is unchanged. The old layout (no `--stack`) is unchanged.
- **AC4.** In every copied text of the `--stack` output, `design/app/prototype.html` reads `docs/design/prototype.html`, and no copied text names `design/app/`.
- **AC5.** The `[paths]` table written by `--stack` has `spec_pr_dirs = ["docs/intent", "docs/specs", "docs/design"]` and `flow_dirs` also lists `"docs/design/"`.
- **AC6.** In the `--stack` output, `.claude/project-instructions.md` says the spec pull request changes only `docs/intent/`, `docs/specs/` and `docs/design/`, and the fast-lane design pull request changes only `docs/design/prototype.html`.
- **AC7.** The `--stack` output has `docs/design/README.md` with one line: `The clickable prototype of the whole app, prototype.html (ADR-030); one file, every screen and state.`
- **AC8.** Every test on `main` passes unchanged, except the tests listed in the issue under `## Existing tests that change`.

Template and kickoff (hand task T2, in `agent-flow-starter` and the project files):

- **AC9.** A pull request into `hungle-agilityio/agent-flow-starter` refreshes it from `bootstrap.py --stack other` run on `main` after T1 (same values as the template: repo `hungle-agilityio/agent-flow-starter`, name `Agent flow starter`, slug `starter`), keeping the template's own files: `.flow/loop/setup_project.py`, `.flow/loop/stacks/`, `.flow/loop/tests/`, `scripts/setup-project.sh`, `README.md`.
- **AC10.** In that pull request `docs/decisions/` has ADR-008 to ADR-033 and the template's tests pass (`uv run --with pytest pytest .flow/loop/tests -q`), with the plugin version raised above `1.0.1`.
- **AC11.** The kickoff instructions (`/mnt/project-files/new-project-setup/kickoff-instructions.md` and the Notion page "Những gì cần cho một dự án mới") have a Prototype step after the idea: Claude builds `docs/design/prototype.html` for the whole app from `idea.md`, posts a card "Prototype ổn (đề xuất) / Sửa", and the first epic is split only after "Prototype ổn"; the prototype is merged with the bootstrap pull request.
- **AC12.** The Notion page "Nguồn của flow" says the template has ADR-008 to ADR-033 and the date of the refresh.

## Edge cases

- Empty: a source decision record that is missing is reported and skipped, as for every manifest entry today.
- Large data: n/a.
- Permissions: only the owner merges the template pull request (hand-built).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| How is the template refreshed? | Fix `bootstrap.py`, then regenerate the template | Patch the template by hand; docs only | The template comes from the bootstrap; fixing the source keeps the next refresh a re-run |
| Q1 Where is the prototype of a new project? | `docs/design/prototype.html`, in the spec pull request | `design/app/prototype.html` at the root | All documents live in `docs/` in the new layout |
| Q2 Does the kickoff build a prototype? | Yes, after the idea, with "Prototype ổn" before the first epic | No, the first visible request makes it | Same rule as ADR-030 for ReviewRadar |
| Q3 Which decision records go in the template? | ADR-020 to ADR-033 copied from `main`, paths moved by the bootstrap | Hand-written generic texts | One source; a re-run refreshes them |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
