# Design

One folder per feature that users will see, `design/<feature>/`. Its `README.md` links the design card (a private artifact showing the normal, empty, error and narrow-screen states with demo data) and notes anything the build must match. Screens, texts and numbers here are demo data only, never customer data.

It is part of the spec pull request (ADR-012). The loop's `capture-before-after` compares the built screens with it.
