# Spec: loop-verify-failures

## Summary

Nothing visible to users of ReviewRadar. Three changes to the flow: the hook `before-skill-script-allow` tells a loop build how to run a plugin skill script it refused, the verify-report input files move to `out/verify-input/`, four permissions the builds needed are allowed, and a new script lists the existing tests an issue's ACs would change so the issue writer can name them.

## Acceptance criteria

### Hook and skills (plugin agent-flow)

- **AC1.** In loop mode (`FLOW_LOOP=1` or `REVIEWRADAR_LOOP=1`), when a Bash command names a `.py` file directly inside `skills/<skill>/` of the plugin (after resolving its real path, as today) but is not one plain launcher call, `before-skill-script-allow.py` answers `permissionDecision: "deny"` with a reason that starts `Run the agent-flow skill script as one plain command` and says: no shell variable, no `;`, `&&`, pipe, redirection or `2>&1`, absolute script path, input files as relative paths such as `out/verify-input/criteria.json`. Examples it covers: `S=/private/tmp/x; uv run python <plugin>/skills/build-verify-report/build_report.py --criteria $S/criteria.json`, and `uv run python <plugin>/skills/build-verify-report/build_report.py --no-ui 2>&1 | tail -30`.
- **AC2.** Outside loop mode the hook behaves exactly as today (allow a plain call, no answer otherwise). A plain call is still allowed in both modes. A command that names no plugin skill script gets no answer in both modes.
- **AC3.** The work-queue skill (step 8.1 and the redo round in section 1) and the build-verify-report skill say: write the criteria file to `out/verify-input/criteria.json` and the screens file to `out/verify-input/spec.json` with the Write tool, and run `build_report.py` with those relative paths as one plain command. The word "scratchpad" no longer appears in the verify step.
- **AC4.** The plugin version is raised to `1.0.9`.

### Permissions (`claude-code-training-lab/.claude/settings.json`)

- **AC5.** `permissions.allow` gains `Read(~/.claude/plugins/cache/ai-training/agent-flow/**)`, `Bash(uv sync:*)`, `Bash(git mv:*)` and `Bash(git cherry-pick:*)`. Nothing else in the file changes.

### Existing tests an issue changes (`ops/`)

- **AC6.** `uv run python ops/pinned_tests.py <issue body file>` (run from `claude-code-training-lab/`) reads the issue body and prints, one per line, `- \`<path>::<test_name>\`: <reason>` for each existing test function under `reviews/tests/`, `ops/tests/` and `../plugins/agent-flow/` that:
  - (a) contains, in its own source or in a module-level helper of the same file that it calls, a backticked name from the issue body that is a Python identifier or a file name (for example `epic_prompt`, `bulk_create`, `location.html`); reason `names <name>`; or
  - (b) uses `django_assert_num_queries` or `assertNumQueries` while a file under "Files likely touched" that is not marked `(NEW)` is a view, a template, a service or a repository under `reviews/`; reason `query count`.
  Names shorter than 4 characters and common words (`main`, `None`, `True`, `False`) are ignored. Paths marked `(NEW)` are never matched as names.
- **AC7.** When nothing matches it prints `No existing test pins this task.` It always exits 0, never writes a file, and never runs the tests.
- **AC8.** Checked against real cases on main: the body of #327 lists `ops/tests/test_epic_stacked_start.py::test_a_task_with_two_dependencies_in_the_epic_branch_starts_on_it` (names `epic_prompt`); a body naming `bulk_create` lists `reviews/tests/unit/test_review_create_paths.py::test_reviews_are_created_only_through_the_repository`.
- **AC9.** `ops/README.md` says the issue writer runs the script before `agent:ready` and copies each test that really changes, with its new value, under `## Existing tests that change`.

## Edge cases

- Empty: an issue body with no backticked names and no touched view lists nothing (AC7).
- Large data: the scan reads only `.py` test files; it finishes in a few seconds on the current suite (about 800 tests).
- Permissions: the hook never allows more than today; AC1 only replaces a dead-end prompt with a refusal that names the plain form.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Hook answer to a non-plain skill-script command | Deny with the plain form, loop mode only | B: accept `S=...;`, `2>&1`, `| tail`; C: no change | #314 and #302 passed once they retried with one plain command; the message is what was missing, not more power |
| Q2. Where the criteria and screen files go | `out/verify-input/` (relative, git-ignored, Edit allowed) | B: keep the scratchpad | The long scratchpad path is why builds use a variable |
| Q3. Permissions to add | Read plugin cache, `uv sync`, `git mv`, `git cherry-pick` | B: only Read and `uv sync`; C: none | All four were refused in the logs (#302, #256, #224, #132) and act only inside the worktree; the commit and push hooks still run |
| Q4. ACs that clash with existing tests | `ops/pinned_tests.py` plus a Definition of Ready line | B: the loop raises query counts itself; C: the DoR line only | Existing tests stay read-only for the loop; the clash is caught when the issue is written (#132, #246, #301, #316, #327) |

## Design

Nothing visible to users.

## Open questions
