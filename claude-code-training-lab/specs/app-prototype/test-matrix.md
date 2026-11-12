# Test matrix: app-prototype

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | Given the spec pull request, when the owner opens the Artifact, then each screen of AC1 is reachable from the menu or a link, with Airport, Downtown and Riverside and 14 reviews. | manual | n/a: checked at "Merge PR spec" | spec |
| M2 | AC2 | normal | Given `#dashboard`, when the page shows, then the seven numbers of AC2 are shown. | manual | n/a: checked at "Merge PR spec" | spec |
| M3 | AC3 | normal | Given `#reply-1`, when the owner presses Use template, Suggest a reply, then Save reply, then the box fills, a loading state shows, and Reply drafts shows "Reply saved." and 4 reviews. | manual | n/a: checked at "Merge PR spec" | spec |
| M4 | AC4 | empty | Given `?bare#dashboard-empty`, when the page shows, then it reads "No locations yet" and no prototype bar is shown. | manual | n/a: checked at "Merge PR spec" | spec |
| M5 | AC5 | normal | `design/app/README.md` lists 33 state ids and the Artifact link; `design/README.md` no longer names `capture-before-after`. | manual | n/a: checked at "Merge PR spec" | spec |
| M6 | AC6, AC7 | normal | Given a spec step with `"design": "dashboard"` and a prototype file, when the report is built, then `report.html` has "Design vs build" with `Design: dashboard` and `Build: dashboard`, and both images have the same size. | integration | `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py` | T1 |
| M7 | AC8 | empty | Given a spec with no `"design"` step, when the report is built, then `design_pairs` is `[]` and `report.html` has no "Design vs build". | unit | `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py` | T1 |
| M8 | AC9 | error | Given `"design": "no-such-state"`, when the report is built, then the row says `Design not found: no-such-state`, `design_screenshot` is `null`, and the verdict equals the one without the key. | unit | `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py` | T1 |
| M9 | AC9 | error | Given no prototype file, when the report is built, then every design row says `Design not found` and the exit code is unchanged. | unit | `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py` | T1 |
| M10 | AC10, AC11 | edge | Given `--design <tmp file>` and a spec `viewport` of 390x844, when the design is captured, then the file given is opened with `?bare#<state>` at 390 by 844 and no verdict field reads the design pairs. | unit | `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py` | T1 |
| M11 | AC12 | normal | `work-queue/SKILL.md` and `write-issue/SKILL.md` contain the `"design"` key text of AC12, and no file of the plugin says `capture-before-after` compares with the design. | unit | `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py` | T1 |
| M12 | AC13 | normal | The plugin version is one patch above the base branch. | unit | `ops/tests/test_check_plugin_version.py` (existing, unchanged) | T1 |
| M13 | AC14 | normal | The `## Design` placeholder of the spec template is the text of AC14. | unit | `ops/tests/test_spec_templates_prototype.py` | T2 |
| M14 | AC15 | normal | The `## Screens to capture` example in the tasks template has a `"design"` key and parses as JSON. | unit | `ops/tests/test_spec_templates_prototype.py` | T2 |
| M15 | AC16 | normal | ADR-030 exists and the decisions README lists it. | manual | n/a: built by hand, checked in its pull request | T3 |
| M16 | AC17 | normal | `project-instructions.md` has the Prototype step, the fast-lane `design:` pull request, and the new Definition of Ready line; "design card" no longer appears. | manual | n/a: built by hand, checked in its pull request | T3 |
| M17 | AC18 | normal | The "Removed, and why" row exists; the Project settings text is given as a file. | manual | n/a: built by hand, checked in its pull request | T3 |
| M18 | AC19 | narrow screen | Given the demo dashboard at 390 px, when it loads, then `scrollWidth` is 390 and the Location scores table scrolls inside its panel. | browser | the issue's `## Screens to capture` (verify report) | T4 |
| M19 | AC19, AC21 | normal | `app.css` served at `/static/reviews/app.css` contains the rule `.grid > * { min-width: 0; }`. | integration | `reviews/tests/integration/test_dashboard_narrow.py` | T4 |
| M20 | AC20 | empty | n/a: an empty account shows the "No locations yet" panel, which has no grid; the 1280 px dashboard of the demo data keeps both panel widths (verify report screenshot). | browser | the issue's `## Screens to capture` (verify report) | T4 |
