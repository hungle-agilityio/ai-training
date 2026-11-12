# Intent: guard-list-one-source

## Problem

The list of files the loop may not change on its own (the guarded files, ADR-023) is written twice: in the plugin hook `before-edit-check.py`, which refuses the edit, and in `ops/epic_pull_request.py`, which lists the guarded files a pull request changed under `## Guard files changed`. A change to one copy and not the other makes the hook and the pull request disagree (retro issue #486). The analysis also found that `ops/flow.toml`, which holds `checks.protected_test_dirs`, is not guarded at all, so a build could change which tests are protected.

## Goal

One list, in the plugin (which the loop cannot change), read by the hook and by `ops/epic_pull_request.py`; `flow.toml` is on it.

## Users

The owner, who reviews the `## Guard files changed` section of loop and epic pull requests and relies on the hook.

## Out of scope

- Which kinds of files are guarded, apart from adding `flow.toml`.
- How a listed file is allowed (`FLOW_ALLOWED_EDITS`, ADR-023, unchanged).
- Any change to the app.
