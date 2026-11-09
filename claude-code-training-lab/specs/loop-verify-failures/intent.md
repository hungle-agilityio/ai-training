# Intent: loop-verify-failures

## Problem

Loop builds finish the code and the tests and then stop without a pull request. Between 2026-11-04 and 2026-11-09 this happened to #224, #225, #302 (twice), #315, #316 and #327, and nine other builds lost turns on the same causes before they recovered. Each stop leaves an issue on `agent:running` or `agent:failed` that the owner has to unblock by hand. The causes, from the run logs in `~/.reviewradar/runs/done/` (analysis: `/mnt/project-files/loop-verify-failures/analysis.md`):

1. The command that builds the verify report is refused ("This command requires approval") when the build writes it with a shell variable, a `;`, a pipe or `2>&1`. Only one plain command runs without a prompt, and the refusal does not say so, so the build stops instead of retrying.
2. The criteria and screen files go to the scratchpad, a long `/private/tmp/...` path, which is why builds put it in a variable.
3. A build cannot read the installed plugin's own files, and `uv sync`, `git mv` and `git cherry-pick` need approval.
4. An acceptance criterion changes something an existing test pins (a query count, an exact prompt text, an architecture rule), the issue does not list that test under `## Existing tests that change`, and the build may not edit it.

## Goal

A loop build that has working code reaches the pull request: the verify-report command runs the first time or is corrected by the hook's message, and issues name every existing test their ACs change before they get `agent:ready`.

## Users

The owner (fewer stuck issues), the loop builds, and the Project threads that write issues.

## Out of scope

- Usage limits, sign-in, reboots and the 45-minute stop (fixed earlier: CLAUDE_CONFIG_DIR, launchd, stale `agent:running` self-heal).
- Letting the loop edit existing tests on its own.
- Changing `build_report.py` itself or the share gate.
