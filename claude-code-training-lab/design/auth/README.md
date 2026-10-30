# Design: auth

Design card: https://claude.ai/artifact/JLAyry3oArssECJLnAfzwx

Four boards, demo data from `seed_demo_data` and the account `demo`:

1. **Normal:** the sign-in page at `/login/?next=/dashboard/`, a centred card with no sidebar, Username focused.
2. **Error:** wrong username or password; Django's message in a red box above the fields, the username kept, the password cleared.
3. **Signed in:** the dashboard with "Signed in as **demo**" and a "Sign out" button at the bottom of the sidebar.
4. **Narrow screen:** the sign-in card and the account block at 360px.

The build must use the texts shown on the card (they are also in `specs/auth/spec.md` AC5, AC6 and AC17) and the app's own colours from `app.css`, in light and dark. The dashed pink outline only marks what is new.
