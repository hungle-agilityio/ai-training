# Intent: verify-screenshots

## Problem

The verify report that comes with every loop pull request always shows the same five screenshots: the dashboard, the reviews page, the Bad and Good filters and a filter with no match. This happens whatever the task changed. A task that changes no page still gets these five pictures, and a task that changes a page gets no picture of that page. When the owner reviews a pull request, the pictures are no evidence of the change. Examples: PR #198 (`ops/flow.toml`) and PR #203 (monthly numbers, no page yet).

## Goal

When a task changes a screen, the report shows that screen and a close-up of the part that changed. When a task changes no screen, the report has no screenshots. When the build cannot capture the screen the task names, no pull request is opened.

## Users

The owner, who reviews loop pull requests from the verify report link.

## Out of scope

- `capture-before-after` (before and after pairs) does not change.
- How the masking scan finds personal data does not change.
- Issues that already exist do not change automatically (see the Edge cases in spec.md).
