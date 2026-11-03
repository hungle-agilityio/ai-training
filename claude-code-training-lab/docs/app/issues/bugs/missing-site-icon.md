# [BUG] Every page asks for a site icon that does not exist

- **Reporter:** Hung Le, project owner
- **Reported on:** 2026-11-03
- **Type:** Bug
- **Labels:** `bug`, `layout`, `ui`, `severity: low`, `reproduced`, `env: dev`

## Summary

When any ReviewRadar page opens, the browser asks for the small icon shown in the browser tab, and the app answers "not found". The tab shows the browser's blank icon, and the browser's error list shows one error on every page. That error hides real errors when someone checks a page for problems. When this is fixed, every page shows a ReviewRadar icon in the tab and the browser reports no error.

## Steps to reproduce

1. Open the sign-in page.
2. Look at the browser tab, then at the browser's error list (developer tools, Console).
3. Sign in as `demo` and open the Dashboard, the Reviews page and the page of the location Airport.
4. Look at the browser tab and the error list on each page.

## Expected result

| Page | Tab icon | Errors in the list |
|---|---|---|
| Sign in | ReviewRadar icon | none |
| Dashboard | ReviewRadar icon | none |
| Reviews | ReviewRadar icon | none |
| Location Airport | ReviewRadar icon | none |
| A page that does not exist | ReviewRadar icon | only the "not found" of that page |

## Actual result

Every page shows the browser's blank icon in the tab, and the error list shows "Failed to load resource: the server responded with a status of 404 (Not Found)" for the address `/favicon.ico`.

## Environment

dev, Chrome (headless and desktop)

## Attachments

Seen on 2026-11-03 while checking the Dashboard, the location page and the Reviews page in a browser: the only error on those pages was this one.
