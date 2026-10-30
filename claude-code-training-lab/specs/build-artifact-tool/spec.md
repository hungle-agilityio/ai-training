# Spec: build-artifact-tool

## Summary

The wrapper that runs one loop build (`run_build` in `ops/agent_tick.py`) reads the tool list that `claude -p` reports when it starts. When `Artifact` is missing, it stops that session at once and starts it again, at most three starts in total. It also keeps the whole session as a log and tells the session how to load a deferred `Artifact` tool. The `work-queue` skill checks for the tool before any work, in loop mode and in an interactive session, so a session without it stops before it builds. Nothing visible to users of the app.

## Acceptance criteria

- **AC1. Command.** `run_build` starts `claude -p <prompt> --max-turns 80 --output-format stream-json --verbose --allowedTools Artifact --append-system-prompt <HINT>`, in the same folder, with `REVIEWRADAR_LOOP=1`, stdin from `/dev/null` and its own process group, as today. The prompt the tick passes is unchanged (`Use the work-queue skill for issue #N only.` and the pull request form). No flag that skips permission prompts is added.
- **AC2. Hint.** `HINT` is a constant at the top of `ops/agent_tick.py` with exactly this text: `If the Artifact tool is listed only as a deferred tool, load it with ToolSearch (query "select:Artifact") before you decide that it is missing.`
- **AC3. Session log.** Each start writes every line of its standard output, unchanged, to `session-<n>.jsonl` in the run folder (`session-1.jsonl` for the first start, `session-2.jsonl` for the second, ...). The run folder is archived to `runs/done/` as today, so the logs are kept.
- **AC4. log.txt stays readable.** `log.txt` in the run folder gets, for each start: one line `start <n> of 3`, the standard error of that start, and the `result` text of the `{"type": "result", ...}` event when there is one. A line of standard output that is not JSON is also copied to `log.txt`. So the last 20 lines that the tick posts on a failed issue, and the plan-limit check, read the final message as today.
- **AC5. Detect a missing tool.** The first event with `"type": "system"` and `"subtype": "init"` carries a `tools` list. When that list does not contain `Artifact`, the wrapper writes `start <n>: no Artifact tool, stopped` to `log.txt`, stops the process group (SIGTERM, then SIGKILL after 30 seconds, as for the time limit) and starts again. When the list contains `Artifact`, or no init event comes before the stream ends, the start runs to its end as today.
- **AC6. Give up after three starts.** When the third start also has no `Artifact` tool, the wrapper writes the outcome `no-artifact` to the `exit` file. The tick (`handle_end`) treats it like any other failed build with the reason `started 3 times without the Artifact tool`: an issue gets `agent:failed`, the comment with the last 20 lines of `log.txt` and one ntfy message; a pull request run gets the "stopped" ntfy. It is never taken as the plan limit, and nothing waits 60 minutes.
- **AC7. Time limit.** The 45-minute limit counts from the first start and covers all starts. When it is reached, the running start is stopped as today and the outcome is `timeout`.
- **AC8. Tests.** A new test file `ops/tests/test_build_artifact_tool.py` covers AC1 to AC7 with `subprocess.Popen`, `os.killpg` and the clock faked (no `claude`, no network): a start with `Artifact` in the init tools (one start, exit code written, `session-1.jsonl` holds the stream, `log.txt` holds the result text); a first start without it and a second with it (two starts, two session files, the stop line in `log.txt`); three starts without it (`no-artifact`, and `handle_end` labels the issue `agent:failed` with the new reason and does not pause); a stream with no init event; a non-JSON line; the time limit reached during the second start. The issue permits editing exactly two existing tests in `ops/tests/test_agent_tick.py`, `test_build_runs_claude_in_loop_mode_with_a_time_limit` and `test_build_is_stopped_after_45_minutes`, only so that they fit the new command and the read of standard output; what they check stays the same. All other existing tests stay unchanged and pass. `uv run ruff check .` and `uv run mypy .` pass.
- **AC9. How to read it.** `ops/README.md` says in a few lines: where `session-<n>.jsonl` is, how to see the tools a build had (`grep '"subtype":"init"'`), what `start <n>: no Artifact tool, stopped` and the reason `started 3 times without the Artifact tool` mean, and that the session is told how to load a deferred `Artifact` tool.

- **AC10. Check the tool first (work-queue).** `.claude/skills/work-queue/SKILL.md` gets a step "Check the tools" that runs before anything else in a run, in loop mode and in an interactive session alike: when `Artifact` is not in the session's tools, load it with ToolSearch (`select:Artifact`); when it is still not there, stop the run before any claim, branch, build, label or comment, and end with the one line `No Artifact tool in this session; nothing was started.`
- **AC11. No agent:failed from that stop.** The stop of AC10 adds and removes no label and posts nothing on GitHub. In an interactive session the issue keeps its labels as they were. In loop mode the tick decides the label as in AC6 (the build ends without a pull request); the session itself never sets `agent:failed` for a missing `Artifact` tool.
- **AC12. Pitfall.** `.claude/knowledge/KNOWN_PITFALLS.md` gets an entry "A session that starts without the Artifact tool" (symptom: #64 and #103 built, passed and ended `agent:failed` with "this session has no Artifact tool", also in a local session; cause: not known yet, intermittent; fix: AC5 restart in the loop, AC10 check first everywhere, and `session-<n>.jsonl` to find the cause).

## Edge cases

- Empty: a start that prints nothing and exits: no session lines, `log.txt` gets the start line and standard error, the exit code is written as today.
- Large data: a session log can be several MB per build; it is kept in `runs/done/` like `log.txt` today, and nothing cleans it.
- Permissions: no new permission. `--allowedTools Artifact` repeats what `.claude/settings.json` already allows; the hook `before-artifact-publish` still checks every publish.
- The tool is in the init list but deferred, and the session still says it is missing: AC2's hint should prevent it; if not, the build ends `agent:failed` as today, and `session-<n>.jsonl` shows whether it tried ToolSearch.
- A plan-limit message during a start: the start ends as today, and the tick's plan-limit check reads `log.txt` (AC4).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Detect at start | Stream output, read the init tool list, stop and start again when `Artifact` is missing (3 starts at most); add `--allowedTools Artifact` | No detection | Costs seconds, before any work; the stream also keeps the session log that was missing for #103 |
| Q2. Resume after a report-step failure on the kept branch | Not in this work | Tick resumes at step 8 in the kept worktree | Q1 stops the run before it spends work; resuming needs a `.claude/` skill change |
| Q3. Fallback when there is no link | None; "no link, no pull request" stays | Pull request without link and `pr:blocked` | The owner expects a report link on every loop pull request |
| Q4. Deferred tool | A fixed hint through `--append-system-prompt` | No hint | Covers the other likely cause without changing the tick's prompt or `.claude/` |
| Q5. Probe on the Mac mini first | Skip | Read the #103 transcript through Remote Control first | Q1 and Q4 cover both likely causes, and the new session log shows the real one next time |
| Q6. A local (interactive) session without the tool | `work-queue` checks the tool before any work and stops without a label (T2, `agent:manual`) | Keep T1 only | The owner saw the same failure in a local build, which the tick's wrapper does not cover |

## Design

Nothing visible to users.

## Open questions
