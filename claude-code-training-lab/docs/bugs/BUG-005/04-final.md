# [BUG] Reply drafts come out in the wrong language

- **Reporter:** Hana, QA
- **Reported on:** 2026-10-13
- **Type:** Bug
- **Labels:** `bug`, `reply-suggestions`, `wrong-output`, `intermittent`, `reproduced`, `env: staging`

## Summary

On the review detail page, the "Suggest reply" button sometimes writes the reply in a different language than the review. In testing, 6 of 20 replies were wrong, always for Vietnamese, French or mixed-language reviews; English reviews were always right. The reply must be in the same language as the review.

## Steps to reproduce

1. On staging, open the detail page of a review written in Vietnamese: "Nhân viên rất thân thiện nhưng phải chờ lâu."
2. Click **Suggest reply**.
3. Read the reply and note its language.
4. Click **Suggest reply** again 10 times on the same review and note the language each time.
5. Repeat with the French review "Très bon service, merci !" and with the mixed review "Great doctor, but chờ lâu quá".

## Expected result

Every reply is in the language of the review: Vietnamese for the Vietnamese review, French for the French one. For the mixed review, the expected language is not decided yet.

## Actual result

The language of the reply changes between attempts on the same review.
- The Vietnamese review "Nhân viên rất thân thiện nhưng phải chờ lâu." got an English reply.
- The French review "Très bon service, merci !" got an English reply.
- The mixed review "Great doctor, but chờ lâu quá" got a Vietnamese reply.
- Over 20 reviews, 6 replies were wrong. English reviews were always answered correctly.

## Environment

Staging. The feature is not available on the dev environment, which currently has only the Dashboard page.

## Attachments

Screenshots from the reporter of the three examples above.
