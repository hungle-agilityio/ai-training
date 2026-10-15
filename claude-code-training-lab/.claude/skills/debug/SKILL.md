---
name: debug
description: Diagnose a bug in ReviewRadar from evidence: reproduce it, trace the call chain from view to repository, find the cause, and propose the smallest fix. Use when a ticket reports a wrong value, a crash, a slow page, or when a test fails and the cause is unclear.
---

# Debug

1. **Reproduce** with the exact steps and data from the ticket. Write down what you saw (values, texts, query count). If you cannot reproduce it, say so; do not guess.
2. **Trace** the call chain: view → form → service → repository → model. Check the likely pitfalls first: `knowledge/KNOWN_PITFALLS.md` (rounding, pagination ties, time zone, N+1).
3. **Find the cause** with one piece of evidence per step (a printed value, a query log, a failing test). Change one thing at a time.
4. **Prove it** with a failing test before the fix (`testing` skill).
5. **Fix at the right layer:** a rule goes in the service, a query in the repository, never in the view.
6. **Report:** symptom, cause, fix, the test that covers it. Add a pitfall entry if it can happen again (`/learn`).
