# Spec: verify-screenshots

## Summary

The verify report shows only the screens a task names. Each step gives a full-page screenshot plus a close-up of the changed element. Tasks without UI get no screenshots. Nothing changes for app users: only the loop's verify step, the browser check and the issue format change.

## Acceptance criteria

### Browser check: close-up of an element (T1)

- **AC1.** A spec step may give `"capture": "<css selector>"`. The browser check then saves two screenshots for that step: the full page `NN-<name>.png`, as today, and the element alone `NN-<name>-element.png`. Both are listed in `result.json` (`screenshot`, `element_screenshot`).
- **AC2.** If the `capture` selector matches nothing, or matches an element that is not visible, the step fails with `capture: no visible element for <selector>`. The run exits with 1 and keeps no element screenshot.
- **AC3.** The masking scan covers the element screenshot's step exactly as it covers the full page. A finding deletes both screenshots of that step.
- **AC4.** A step without `capture` behaves exactly as today, and every existing check-in-browser test passes unchanged.

### Verify report: only the named screens (T2)

- **AC5.** `build_report.py --no-ui` runs no browser. The Browser axis reads `NOT APPLICABLE` with the evidence `the task changes no screen`, and the report shows no "Screenshots" section. `NOT APPLICABLE` does not make the verdict `INCOMPLETE`.
- **AC6.** With `--no-ui`, the report's masking status is `clean` when no report text (title, criteria, review) holds personal data, and `findings` otherwise. The share gate then allows the link with no change to `share_gate.py`.
- **AC7.** `build_report.py --browser` without `--spec` no longer falls back to the default pages. The Browser axis is `FAIL` with `no screens given: pass --spec from the issue's "Screens to capture"`, and the verdict is `FAIL`.
- **AC8.** With `--browser --spec`, the report shows each step's full-page screenshot next to its element screenshot, captioned with the step name and `(close-up)`.
- **AC9.** A failed `capture` (AC2) makes the Browser axis `FAIL` and names the step.
- **AC10.** `--browser` and `--no-ui` together are refused (exit 2, usage message).

### Loop and issues (T3)

- **AC11.** Every issue labelled `needs-ui` has a `## Screens to capture` section holding one fenced `json` block. The block is a check-in-browser spec (`{"steps": [...]}`) in which every step has `goto` and `capture`. The issue templates (`docs/app/templates/task.md`, `feature.md`, `bug.md`), `write-issue` and the spec `tasks.md` template describe this section.
- **AC12.** `work-queue` step 8.1: for an issue with `needs-ui`, the build copies that block unchanged into a file and runs `build_report.py --browser --spec <file>`. For an issue without `needs-ui`, it runs `build_report.py --no-ui`.
- **AC13.** A `needs-ui` issue that has no `## Screens to capture` block, or whose block is not valid JSON, opens no pull request. The issue gets `agent:failed` and a comment (with the marker): `needs-ui but no valid "Screens to capture" block`.
- **AC14.** A report whose Browser axis is `FAIL` (AC7, AC9) opens no pull request, as for any `FAIL` verdict: `agent:failed` and a comment naming the step.
- **AC15.** `/verify` (`.claude/commands/verify.md`) says: no UI means `--no-ui`; UI means `--browser --spec` from the issue. (T1 and T2 update their own SKILL.md files the same way.)

## Edge cases

- Empty: a `needs-ui` issue whose block has `"steps": []` is treated as missing (AC13).
- Large data: a long page is still captured full page. The close-up keeps the element's own size, with no limit.
- Permissions: the steps run signed in as `demo`, as today. A step for the sign-in page sets `"sign_in": false` in the spec object.
- Open issues already labelled `needs-ui` and `agent:ready` before T3 is merged have no block. Before T3 is merged, a thread adds the block to each of them. The tick holds those issues until then, through `Depends on #<T3>`.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Task without UI: screenshots? | No screenshots; Browser `NOT APPLICABLE`; masking scans report text only | Default pages labelled "not related"; always one dashboard shot | Unrelated pictures are noise; the text scan still keeps personal data out |
| Q2 Where do the screens come from? | `## Screens to capture` in the issue, written at spec time, copied to `--spec` | Build infers from the diff; issue first with inference as fallback | The owner approves the screens in the spec; the build does not guess |
| Q3 What is captured? | Full page plus a close-up of the named element | Element only; full page only | The close-up shows the change, and the full page shows where it sits |
| Q4 UI task where the right part cannot be captured | Browser `FAIL`, no pull request, `agent:failed` | `INCOMPLETE`, pull request with a warning | Evidence of the wrong screen makes the review worthless |
| (spec) Format of the section | A fenced JSON check-in-browser spec | Free text that the build turns into steps | Copied unchanged, so the build has no room to interpret |

## Design

Nothing visible to app users. The report layout changes only by adding the close-up next to each full-page screenshot (AC8).

## Open questions
