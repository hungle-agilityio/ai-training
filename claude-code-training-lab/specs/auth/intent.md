# Intent: auth

## Problem

Anyone who has the link can open ReviewRadar today: the dashboard, the review list with customer texts, the CSV export and the JSON API are all public, on the live Render site too. A business cannot keep its customer reviews to its own staff.

## Goal

Only people with an account can see ReviewRadar. They sign in with a username and password, see every page as today, and sign out from the sidebar. The live demo stays usable with one demo account whose password is set on Render, not in the code.

## Users

- Business staff and the owner of ReviewRadar, who sign in.
- The ReviewRadar admin (the owner), who creates accounts and resets passwords with a command.

## Out of scope

- Sign-up by visitors, and Django's admin site.
- Roles or access per business or per branch: every signed-in user sees every branch.
- Password reset by email.
- Locking an account after wrong passwords (a follow-up; see Decisions in `spec.md`).
- A custom user model or any change to the `reviews` models.
