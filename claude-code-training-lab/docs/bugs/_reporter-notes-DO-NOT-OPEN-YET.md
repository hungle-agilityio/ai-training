# Reporter notes: facts the reporter knows

Do not read this file during the morning analysis. It is the source for role-playing the
reporter: give it to Claude and ask it to answer your clarifying questions using ONLY these
facts, and to say "I don't know" for anything not listed.

## BUG-001 (Maria)
- Looked at the Riverside branch. Its reviews are 4, 5 and 2 stars; she averaged them by hand.
- The other branches matched her numbers; only Riverside did not.
- Seen on her laptop (Chrome, macOS) at the /dashboard/ page of the local app.
- She first noticed it this week; she does not know if it was always like this.

## BUG-002 (Tom)
- About 50 branches loaded. With the 3 demo branches it is fast.
- He opens /dashboard/ in the browser. He did not time it exactly; it felt like 10 seconds or more.
- He does not know whether the slowness is in the page or in the data.

## BUG-003 (Linh)
- She created a branch named "Newtown" yesterday. It has no reviews yet.
- The dashboard shows a server error page (HTTP 500) for everyone.
- Before Newtown existed it worked. She has not tried deleting it.

## FEAT-004 (Marcus)
- "Good" means 4 or 5 stars, "bad" means 1 or 2 stars, 3 stars is neutral.
- Wants the filter on the dashboard, per branch, and a weekly range (Monday to Sunday).
- Does not need export. Wants it in the next sprint.
- Sentiment (good/bad) from the Claude API is not built yet; star rating is acceptable for now.

## BUG-005 (Hana)
- She saw it in the design prototype shared by the designer, not in the running app.
- Example: a Vietnamese review got an English reply. She cannot say how often.
- She does not know which build or branch the prototype was from.
