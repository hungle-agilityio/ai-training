# Design: security-check

Design card: https://claude.ai/artifact/RTLAQpaTaRSav95SBC2HPt

Four boards of the sign-in page at `/login/`, demo account `demo` from `seed_demo_data`:

1. **Empty:** no failed attempt; the page as on `main`.
2. **Normal:** a wrong password (attempts 1 to 5); Django's message as on `main`, the username kept, the password cleared.
3. **Error (new):** the username is locked for 15 minutes; the red box says `Too many failed sign-in attempts. Try again in 15 minutes.`
4. **Narrow screen:** the locked state at 360px; the message wraps inside the card.

The build uses the texts on the card (also in `specs/security-check/spec.md` AC5 and AC6) and the existing `.signin-error` box of `app.css`, in light and dark. The dashed pink outline only marks what is new.
