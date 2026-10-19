# [TASK] Claude Code practices already in place

- **Requester:** Hung Le, project owner
- **Reported on:** 2026-10-19
- **Type:** Task
- **Labels:** `task`, `tooling`

## Summary

A record of the work on the Claude Code practices that is already finished, gathered in one closed issue so that the three epics can point to it. Each finished piece is listed below in plain words. Nothing here is new work. It touches the project's rules, helpers, checks and documents, and nothing visible to users of the ReviewRadar app.

The pieces still open (protecting the main branch, and publishing the epics) have their own issues.

## Scope

- **Included:** all the pieces of work marked as done in the project's list of work on 2026-10-19.
- **Not included:** protecting the repository (partly done, blocked by the GitHub plan); publishing the epics; the optional ideas without a real use yet.

## Done when

Each item below was recorded as done in the project's list of work. A person can check each one by reading the named result.
- [x] Baseline: one naming standard, renamed skills, a way to settle decisions before planning, one file per issue, documents split in two, and a guard that limits GitHub access to one repository.
- [x] Naming finished: helpers renamed, short model names, commands and skills no longer repeat each other.
- [x] GitLab replaced by GitHub in the rules, skills, project map and README.
- [x] The repository tells the truth: dependency versions pinned, README status correct, the demo data command tested.
- [x] Automatic checks on GitHub: style, types, tests, the safety-check tests and a coverage gate.
- [x] Templates and basic files on GitHub: issue forms, pull request template, example settings, contributing note.
- [x] Project map and decision records.
- [x] Workflow rules: four team principles, a two-round limit on AI fixes, guardrails, a mode guide and five review areas.
- [x] A cheap helper that runs the checks and reports only what failed.
- [x] Safety checks and permission lists that refuse forbidden actions.
- [x] Memory: the rule for when to save, and the first saved notes.
- [x] The repository on GitHub with the full history under the owner's account.
- [x] A browser check in verify, with screenshots and a console status.
- [x] The verify report as a local file that opens by itself.
- [x] Sharing the report as a private link, with a privacy and approval rule.
- [x] Before and after screenshots on the same demo data.
- [x] Masking of sensitive data in screenshots and logs, with a scan that stops the run.
- [x] The pull request draft with evidence.
- [x] A page on the flow with outside tools (the list of tools is still an assumption).
- [x] A base layout for skills, with a test for each.
- [x] Each of the three epics (#10, #11, #12) points to this issue for its finished pieces.

## Steps to check the result

1. Open the three epic issues on GitHub.
2. In each epic, find the pieces ticked as done and check that each one is named in the list above.
3. Open the lists of work in the project documents and check that every piece named above shows as done.

## Expected result

Every finished piece of work is named here once, and each epic points to this issue for its finished pieces.

## Environment

dev

## Attachments

Nothing attached. The evidence for each piece is in the commits and pull requests already in the repository.
