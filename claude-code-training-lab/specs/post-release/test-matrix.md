# Test matrix: post-release

The tests planned per AC of [spec.md](spec.md), one row per check (ADR-026).

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | With `RENDER_GIT_COMMIT=5213e391e7ac164d86be3ee74e8a8c4eeba6ad1f`, `GET /healthz/` answers 200, body `ok`, header `X-Commit` with that value, 0 queries | integration | `reviews/tests/integration/test_healthz_commit.py` | T1 |
| M2 | AC1 | empty | With `RENDER_GIT_COMMIT` missing or `"  "`, the response has no `X-Commit` header, body `ok`, 0 queries | integration | same | T1 |
| M3 | AC2 | edge | The variable is read per request: changed between two requests, the header follows | integration | same | T1 |
| M4 | AC3 | normal | `ops/flow.toml` has `[live]` with the four keys and values; `FlowConfig.live` holds them | unit | `ops/tests/test_live_check.py` | T2 |
| M5 | AC3 | empty | A flow config without `[live]` loads, `live` is None; with `[live]` but no `url`, loading stops naming `live.url` | unit | same | T2 |
| M6 | AC4 | normal | `ops/agent.env.example` has `REVIEWRADAR_DEMO_PASSWORD=`, `RENDER_API_KEY=`, `RENDER_SERVICE_ID=`, each after a comment line | unit | same | T2 |
| M7 | AC5 | error | No `[live]`: exit 2, `no [live] table in flow.toml`, no request; blank password: exit 2, `REVIEWRADAR_DEMO_PASSWORD is not set in agent.env` | unit | same | T2 |
| M8 | AC6 | normal | Fake fetcher live on the third poll: prints `live: 5213e39 after 0m40s`, then goes on to the screens | unit | same | T2 |
| M9 | AC6 | error | Never live within 15 fake minutes, header `d7738b4…`: `FAIL wait: 5213e39 is not live after 15 minutes (live: d7738b4)`, `result: fail`, exit 1, no browser started; no header: `(live: none)` | unit | same | T2 |
| M10 | AC7 | normal | Against `live_server` with a two-step spec, the step that finds its texts prints `PASS <name> <s>s` | integration | same | T2 |
| M11 | AC7 | error | The step with a text not on the page prints `FAIL <name>: missing text "<text>"`; a wrong password prints `FAIL sign-in: could not sign in as demo` and stops | integration | same | T2 |
| M12 | AC7 | edge | A fake clock of 3.4 s for one step prints `SLOW <name> 3.4s (over 3s)` and counts as passed | unit | same | T2 |
| M13 | AC8 | normal | Fake answers for the five checks: `PASS https-redirect`, `PASS frame-options`, `PASS hsts`, `PASS login-required`, `PASS healthz` | unit | same | T2 |
| M14 | AC8 | error | Each check failing on its own (200 instead of 301; no `X-Frame-Options`; HSTS with `includeSubDomains`; 200 for `/dashboard/`; 503 for healthz) prints its `FAIL <name>: <reason>` | unit | same | T2 |
| M15 | AC9 | normal | All pass with one SLOW: last line `result: pass, 1 slow`, exit 0; one FAIL: `result: fail`, exit 1; the password value never appears in the output | unit | same | T2 |
| M15b | AC10 | normal | `ops/README.md` has a section `## Live check` that names the three variables, the command and the `result:` lines | unit | `ops/tests/test_live_check.py` | T2 |
| M16 | AC11 | normal | Fixture repo with tags `v2026.11.10`, `v2026.11.11`, `v2026.11.12` and `deploy` at `v2026.11.12`: the target is `v2026.11.11`; with `--to v2026.11.10` it is `v2026.11.10` | unit | `ops/tests/test_rollback.py` | T3 |
| M17 | AC11 | empty | Only one tag: `no earlier release to roll back to`; `deploy` not on a tag: `origin/deploy is not a release tag`; `--to v2026.12.01`: `v2026.12.01 is not an earlier release`; blank key: `RENDER_API_KEY is not set in agent.env`; all exit 1 | unit | same | T3 |
| M18 | AC12 | normal | Fake Render list with two deploys of the target commit (`live`, then `deactivated` newer): the newer one is chosen | unit | same | T3 |
| M19 | AC12 | error | No deploy of the target: `no Render deploy of v2026.11.11 (<sha7>) found`; Render 401: `Render API failed: HTTP 401`; the key is in no output | unit | same | T3 |
| M20 | AC13 | normal | Two migration files between target and deploy, `persistent_database = false`: `Migrations since v2026.11.10: 2 (the live database is rebuilt from demo data at start; nothing to reverse)` | unit | same | T3 |
| M21 | AC13 | edge | Same with `persistent_database = true`: refuses with `2 migrations since v2026.11.10 and the database is persistent: write a reversing migration on main and release it`; no migrations: `Migrations since <tag>: 0` | unit | same | T3 |
| M22 | AC14 | normal | `--dry-run` prints the five parts in order and sends no POST; without it the POST body is `{"deployId": "<id>"}` and the last line names `ops/live_check.py --commit <sha>` | unit | same | T3 |
| M23 | AC15 | edge | After a run, the fixture repo's branches and tags are unchanged and no `git push` was called; no Render call other than the list and the rollback | unit | same | T3 |
| M24 | AC16 | normal | A 200 `ok` answer: state `failures` 0, nothing sent, exit 0 | unit | `ops/tests/test_uptime.py` | T4 |
| M25 | AC16 | empty | No `[live]`: no request, no state file, exit 0 | unit | same | T4 |
| M26 | AC17 | normal | Fail at 09:00, fail at 09:05: one message `ReviewRadar site is down since 09:00 (Vietnam time): HTTP 503`, priority high; a third failure sends nothing | unit | same | T4 |
| M27 | AC17 | edge | Success after the alert at 09:20: `ReviewRadar site is back after 20 minutes`, priority low, state reset; one failure then success: nothing sent; reasons `timeout after 60s` and `no connection` | unit | same | T4 |
| M28 | AC18 | normal | `ops/start-loop.sh` runs `uv run python $REL/uptime.py` after `agent_tick.py` in the loop line, with a failure that does not stop the loop | unit | same | T4 |
| M29 | AC18 | manual | After "dừng loop" and "bật loop" on the Mac mini, `~/.reviewradar/uptime.json` is updated every 5 minutes | manual | (none) | T4 |
| M30 | AC19 | normal | `pyproject.toml` lists `sentry-sdk[django]>=2.40` in `dependencies`; `uv lock --check` passes | unit | `reviews/tests/unit/test_error_tracking.py` | T5 |
| M31 | AC20 | empty | `SENTRY_DSN` blank or missing: returns False, `sentry_sdk.init` not called | unit | same | T5 |
| M32 | AC20 | normal | `SENTRY_DSN` set: returns True, `sentry_sdk.init` called once with every argument of AC20; `before_send` removes `query_string`, `data`, `cookies` | unit | same | T5 |
| M33 | AC21 | normal | `render.yaml` has `- key: SENTRY_DSN` followed by `sync: false` | integration | `reviews/tests/integration/test_render_sentry_env.py` | T5 |
| M34 | AC22 | normal | Given the demo data in the light theme, when the dashboard opens, then a "Goal met" badge has text colour rgb(23, 117, 63) on rgb(224, 245, 234), and the sidebar note has opacity 1 | browser | `ops/tests/test_a11y_check.py` | T6 |
| M35 | AC22 | empty | n/a: only colours change; a screen with no badge or link has nothing that changes, and the empty states keep their texts | manual | (none) | T6 |
| M36 | AC22 | normal | Given the dark theme, when a location page opens, then a plain link has the colour rgb(123, 147, 255) | browser | same | T6 |
| M37 | AC23 | error | A copy of `axe.min.js` with one byte changed: exit 2, `axe.min.js does not match axe-core 4.10.3` | unit | same | T6 |
| M38 | AC23 | normal | Fake axe results: serious → `FAIL <name> light: color-contrast x2 (.badge)`; critical → FAIL; moderate → `NOTE`; none → `PASS`; result line and exit code | unit | same | T6 |
| M39 | AC23 | normal | A one-step spec (`dashboard`, `/dashboard/`) on the app gives `result: clean` for `--scheme light` | browser | same | T6 |
| M40 | AC24 | normal | `checks.yml` has `Accessibility of the main screens` with the exact `run` line directly after `Browser regression of the main screens` | unit | same | T6 |
| M41 | AC25 | edge | A bootstrap into a temporary folder (default layout and `--stack python`) has a `checks.yml` without the step and no `vendor` folder | unit | same | T6 |
| M42 | AC26 | manual | ADR-032 exists with context, decision and the rejected options of Q1 to Q7; ADR-017 has the "Item 5 replaced" line; the README lists ADR-032; `.claude/CLAUDE.md` has the new row | manual | (none) | T7 |
| M43 | AC27 | manual | The Release paragraph runs the live check after `release.py` and shows the rollback card on FAIL; the "rollback" command and the one-time setup paragraph are there | manual | (none) | T7 |

## Allowed values

- "Case" is one of "normal", "empty", "edge", "error", "permission", "narrow screen".
- "Level" is one of "unit", "integration", "browser", "manual".

## Rules

- Every AC has at least one row; AC22 is the only AC users of the app see, and has a "normal" row and an `n/a` "empty" row.
- A row's test file is the new test file named in its task.
- The matrix is part of the spec pull request.
