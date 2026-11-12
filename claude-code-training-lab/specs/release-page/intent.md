# Intent: release-page

## Problem

`ops/release.py` pushes `release/sprint-N`, a `v*` tag and `deploy`, but GitHub shows only the tag, no Release page. The client-facing release notes live only in an artifact page, so clients and the team cannot see what shipped in one place on GitHub (retro issue #490).

## Goal

Each release tag gets a GitHub Release page with the release's pull request list and a link to the release notes page.

## Users

The owner, the team and clients who look at the repository.

## Out of scope

- Rewriting the release notes text for clients (the artifact page keeps it, ADR-029).
- Render's deployment records showing ref `main`: the owner checks Render's Branch setting once (Settings → Build & Deploy → Branch = `deploy`); no code.
- Releases made before this change.
