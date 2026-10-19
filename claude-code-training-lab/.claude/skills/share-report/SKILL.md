---
name: share-report
description: Share a verify report as a private artifact link, only when the sharing gate allows it (masking check clean, standing approval on, demo data only), and say plainly why there is no link when it does not. Use at the end of /verify, or when the user asks to share or send a verification report.
---

# Share a report

A report is built by `build-verify-report` and stays on this machine. Publishing it as an artifact sends its content, screenshots included, to an outside service, so it passes a gate first. The gate is applied by this procedure, and a second layer is the hook `before-artifact-publish`, which blocks the Artifact tool for any file under `out/verify/` unless the gate allows and writes one audit line per call to `out/artifact-publish.log`. The hook was seen firing on the first real publish (2026-10-19). A call that the tool itself rejects first (for example a missing file) never reaches the hook.

## Procedure

1. Take the report folder: `out/verify/<time>/` (it holds `report.html` and `report.json`).
2. Run the gate: `python3 -I .claude/skills/share-report/share_gate.py <report folder>`.
   - `BLOCKED: <reason>` (exit 1): **no link**. Keep the local file, tell the user in one line which condition failed (masking not clean, approval off, page too big, files missing). Do not try another way to publish.
   - `ALLOWED` (exit 0): continue.
3. Publish with the Artifact tool, the file `report-share.html` (the same report written as artifact page content), a short icon word such as `report`, and a one-sentence description. Load the `artifact-design` skill first, as the tool asks; the page already follows its contract (two-word title, colour tokens with dark mode, no horizontal scroll). The artifact is private until the user shares it. If the report was shared before (`share.url` in `report.json`), republish to the same URL.
4. Write the link into `report.json` under `share` (`url`, `date`) and print it.
5. When the issue exists on GitHub, post the link as a comment on the issue (`gh issue comment <number> --body "Verification report: <link>"`). The link goes in a comment, never inside the issue file.
6. Give the user the verdict, the link, and the comment's address.

## Rules

- The rules, and the standing approval the user gave on 2026-10-16, are in `rules.md`: the masking check of the report must be `clean`, only demo data is shown, and the approval can be switched off by editing one line.
- Only verify reports follow this skill. Any other artifact is shared only with the user's approval of that item.
- Never share a report with `masking` missing, `not run` or `findings`. A failing verdict can be shared (it is evidence); a failing masking check cannot.
- What becomes an artifact, and what does not, is in `.claude/CLAUDE.md` ("When something becomes an artifact").
