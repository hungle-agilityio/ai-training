# Intent: post-release

## Problem

After `ops/release.py` moves `deploy`, Render deploys by itself and nobody checks the live site. Three gaps follow from that, and a fourth from the training audit of Day 14 and 15 (2026-11-12):

- **No check after a release.** Every build checks its own screens on a throw-away database, and test-harden adds a browser regression in CI, but nothing opens https://reviewradar.onrender.com after a deploy. A broken start, a missing setting or a page that works locally but not on Render is found by a client.
- **Rollback is a manual click.** ADR-017 says a bad release is undone with Render's Rollback button. That button also turns Auto-Deploy off, so the next release silently does not deploy until someone turns it back on. There is no rule for a release that added migrations.
- **No monitoring.** Render pings `/healthz/` for its own health check, but nobody is told when the site is down, and a server error (500) leaves no trace outside Render's log.
- **No accessibility or speed check.** No check looks at contrast, labels or page speed. A run of axe-core on `main` (fb05984, 2026-11-12) finds `color-contrast` (serious) on 9 of the 10 main screens in the light theme (sidebar note, green and amber badges), and in the dark theme the plain links keep the browser blue (#0000ee) on 6 screens.

## Goal

1. After every release, one command on the Mac mini waits until the released commit is live, signs in and opens the nine main screens, and gives PASS or FAIL with the load time of each screen.
2. One command rolls Render back to the previous release through Render's API, keeps Auto-Deploy on and `deploy` untouched, and refuses when a persistent database would need its migrations reversed.
3. The owner's phone is told within about 10 minutes when the live site stops answering, and again when it is back; every server error reaches Sentry without personal data.
4. CI fails on a serious or critical accessibility finding on the main screens, in the light and the dark theme; the contrast findings of today are fixed.

## Users

The owner, who releases and is called when the site breaks; the clients of ReviewRadar's businesses, who use the live site (and read it better with the contrast fix); the release thread on the Mac mini, which runs the check and the rollback.

## Out of scope

- A check that blocks the release before it is pushed (the security-check thread owns `ops/release.py`).
- Moving `deploy` back or any force push (ADR-017 stays).
- A persistent database on Render, backups or data migration back: the live database is rebuilt from demo data at every start today.
- Performance budgets that fail CI, Lighthouse scores, load tests.
- Paid monitoring, status pages for clients, Sentry performance tracing.
- The template repository `agent-flow-starter`.
