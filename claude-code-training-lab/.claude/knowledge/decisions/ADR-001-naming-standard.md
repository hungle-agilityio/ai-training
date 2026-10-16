# ADR-001: Naming standard

- Status: Accepted
- Date: 2026-10-16

## Context

Names followed no pattern: skills called `git`, `gitlab`, `testing`, `debug`, `pr-review` and `write-ticket`; helpers called `ticket-analyst` next to `implementer`; pinned model versions. The team deck names its skills verb plus object (`generate-docx`, `fix-from-github`).

## Decision

- Skills: verb + object, imperative, kebab-case, at most three words, one job each, no tool or platform name.
- Commands: one lifecycle verb. Helpers: the role as a noun, with the role (advisor, builder, runner) in the description and a short model name (`opus`, `sonnet`, `haiku`). Hooks: `<when>-<purpose>`.
- Words: "issue" and "pull request", never "ticket" and "merge request".
- The table of names lives in `.claude/rules/naming.md`.

## Consequences

Seven skills and two helpers were renamed and every mention was updated. A new name that breaks the pattern is a defect. Anthropic's own guide prefers a gerund form (`writing-issues`); verb + object is also accepted and matches the team deck and how people type commands.
