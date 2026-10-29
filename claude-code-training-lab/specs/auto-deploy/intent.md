# Intent: auto-deploy

## Problem

ReviewRadar only runs on the owner's computer. Nobody can open it from a link, and every merged change has to be run by hand to be seen.

## Goal

The app is online at a free Render address with HTTPS and demo data, and every merge to `main` whose CI is green goes live by itself, with no step by a person.

## Users

The owner, and anyone the owner sends the link to (QA, BA, clients) to look at the demo.

## Out of scope

- A paid plan, a custom domain, or a server that never sleeps.
- Keeping data between deploys: the site always shows the demo data again after a restart.
- Pages that write data, logins, an admin site.
- A deploy job in GitHub Actions; Render waits for the existing `Checks` workflow.
- Changes to the loop, the hooks or `.claude/`.
