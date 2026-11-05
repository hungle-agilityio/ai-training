# Intent: review-replies

## Problem

ReviewRadar shows scores and reviews, but staff cannot answer a review inside the app. They do not know which reviews still need an answer, the worst reviews wait as long as the good ones, and nothing records who wrote an answer or when. The sidebar has shown "Reply drafts" as "Soon" since the start.

## Goal

Staff open "Reply drafts" in the sidebar and see the reviews with no reply yet, worst first and oldest first. They write or edit one reply per review on its own page and go back to the list. The review list shows which reviews have a reply and filters on it, and the dashboard shows how many reviews still need one. The demo data has replies for its good reviews, so every state shows on Render. It goes live at one release after the whole epic is merged.

## Users

- Business staff and owners who are signed in. Every signed-in user sees every location and may write or edit any reply, as with the other pages today.

## Out of scope

- Sending or posting a reply to Google, Facebook or any other site, and e-mail.
- Reply suggestions by AI, templates, or a "mark as sent" state.
- Deleting a reply, a history of edits, or more than one reply per review.
- Roles or permissions per location.
