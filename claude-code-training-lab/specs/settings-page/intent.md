# Intent: settings-page

## Problem

The sidebar has shown "Settings · Soon" since the first version, and it leads nowhere. Staff who want to change their own password cannot: only the admin can reset it on the server (`manage.py changepassword`, spec `auth` Q4). When the "Suggest a reply" button (epic #281) is hidden, staff have no way to see why.

## Goal

The Settings item in the sidebar opens `/settings/`. There a signed-in user sees their username, changes their own password, and sees whether Claude reply suggestions are on, in demo mode or off, and which model they use. Nothing on the page changes a business rule.

## Users

- Every signed-in user (business staff and owners), for their own account only. There is no staff-only part.

## Out of scope

- Editing the username, a display name or an e-mail address.
- A reply signature per location (needs a migration and changes the epic #281 code; a later epic).
- Adding, renaming or removing locations; creating or removing users.
- E-mail alerts for bad reviews (no e-mail service yet).
- Changing the score rules, the week or the good/bad rating ranges (`rules/domain.md`).
- Turning reply suggestions on or off, or entering the API key, from the page: they stay environment variables (spec `reply-suggest` AC1, Q10).
- Locking an account after wrong passwords (as in spec `auth` Q8).
