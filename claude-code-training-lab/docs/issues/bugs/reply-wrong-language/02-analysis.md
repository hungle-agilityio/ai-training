# [BUG] Reply drafts come out in the wrong language: analysis and questions

- **ID:** 5
- **Reviewed on:** 2026-10-14
- **Status:** Waiting for reporter
- **Type:** Bug
- **Labels:** `bug`, `reply-suggestions`, `wrong-output`, `intermittent`, `cannot-reproduce`, `needs-info`, `env: to confirm`
- **Where:** The feature that suggests a reply to a customer review. We don't know which page or screen Hana used. We could not find this feature in the app we have, which currently has only the Dashboard page.

## Analysis (3 sentences)

1. **What it asks:** When the app suggests a reply to a customer review, the reply must be written in the same language as the review.
2. **What is ambiguous:** We don't know where Hana saw the drafts (which page or screen, which version of the app), which languages were involved, what exactly "wrong" means (for example an English reply to a Vietnamese review), or how often it happens. We also could not find the suggested-reply feature in the app we have, so she may have tested another version.
3. **First step:** Ask Hana for 3 to 5 examples where it went wrong (the review, the reply she got, the time, which version) before changing anything. Then look at what these examples have in common, for example the language, a very short review, or a review mixing two languages.

## What we found so far

We could not find the reply-suggestion feature in the app we have (it currently has only the Dashboard page), so we could not reproduce the problem.

## Questions for the reporter

1. Where did you see the draft replies (which page or screen, what address)? Which version of the app and which environment (test or production)?
2. For each wrong case, please send: the review text, the language you expected, the reply you got, the time, and a screenshot.
3. About how many drafts did you try, and how many were wrong (for example 3 out of 20)?
4. Which languages were involved? Were some reviews very short or written in two languages?
5. If you ask for a draft for the same review again, is the result always wrong, or does it change?
