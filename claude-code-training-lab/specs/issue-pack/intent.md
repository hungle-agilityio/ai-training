# Intent: issue-pack

## Problem

The Project turns a request into a spec and issues, and the loop builds them without asking anyone. Three parts of a good issue pack are missing. The spec and the issues have no user story, so a reader does not see who gains what. The acceptance criteria users can see are written "When X, the screen must Y" or as free text, never as Given/When/Then with the starting data. Nobody plans the tests from the criteria before the build: the verify report shows which ACs passed only after the build, so a missing empty case or error case is found late or never. The rule "anyone can follow the issue without asking questions" exists in the `write-issue` skill, but nothing measures it.

## Goal

1. Every new full-lane spec has a user story, Given/When/Then for the ACs users can see, and a test matrix written from the ACs before any build. Each issue names its matrix rows.
2. Before an issue gets `agent:ready`, a fresh agent that knows only the issue and the repository finds zero questions it would have to ask. The number of rounds is recorded.

## Users

The owner, who reads one spec pull request and can now check the tests planned for each AC; the Project thread that writes the spec and the issues; the loop, which builds from the issue alone.

## Out of scope

- Changing specs, issues or tests that already exist; the rules apply to requests started after this change.
- Given/When/Then for technical ACs (a function, a query, a file): they keep today's plain form.
- The verify report or the loop checking matrix rows one by one.
- The CLI issue route (`docs/app/templates/feature.md`, `check_issue.py`): unchanged.
- The template repository `agent-flow-starter`: a separate request later.
