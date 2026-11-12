# Intent: test-harden

## Problem

The Day 14 audit of 2026-11-12 (training "Day 14: Test and harden") found three gaps in how ReviewRadar is tested and reviewed before it reaches clients.

- **Review.** A loop build runs the `reviewer` sub-agent only for Hard issues and Medium issues that hit a trigger. Claude Code's `/code-review` is never part of the flow (it ran once by hand, for #460). Nothing raises the review when a change touches sign-in, data or settings. The epic → main pull request, which carries several tasks at once, gets no Claude review before the owner reads it.
- **QA regression.** CI runs about 2,110 unit and integration tests, and each build checks the screens of its own issue. No check opens the main screens in a real browser on every change, so a template error, a broken link or a console error on a page the build did not touch reaches `main` unseen.
- **Release notes.** `ops/release.py` prints only pull request titles, internal and client-facing mixed. Clients get no plain account of what changed. The release-deploy spec put release notes out of scope.

## Goal

1. Every loop build runs `/code-review` and fixes what it finds; a build that touches a sensitive path (sign-in, data, settings, hosting) gets the review at high effort plus the `reviewer`. Each epic → main pull request gets one high-effort `/code-review` and one round of fixes before the owner reviews it.
2. CI opens the nine main screens in a headless browser on demo data, on every pull request and every push to `main` and `deploy`, and fails on a missing text, a console error or a failed request. A release already waits for green Checks.
3. Each release keeps one living client-facing release notes page up to date: `release.py` separates client-facing pull requests from internal ones, and the release thread adds the new release at the top of the page.

## Users

The owner, who reviews less and trusts more; QA, who gets a browser regression on every change; the clients of ReviewRadar's businesses, who read the release notes; the loop, which builds.

## Out of scope

- Ultrareview in the loop. It is billed per run and needs an interactive session; the owner may run it by hand on any pull request.
- Changing builds, pull requests or releases that already exist.
- Regression of every page state (filters, empty states, errors): those stay in the integration tests.
- Release notes as GitHub Releases, e-mail or a page in the app.
- The template repository `agent-flow-starter`: a separate request later.
