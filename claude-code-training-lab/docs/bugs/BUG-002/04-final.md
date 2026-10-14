# [BUG] Dashboard is very slow

- **Reporter:** Tom, regional director
- **Reported on:** 2026-10-12
- **Type:** Bug
- **Labels:** `bug`, `dashboard`, `performance`, `partly-reproduced`, `env: production`

## Summary

The Dashboard takes about 25 seconds to open on production, with about 500 locations loaded. It was instant in the demo with only a few locations. It must open in under 2 seconds.

## Steps to reproduce

1. With only 3 locations in the system (Airport, Downtown, Riverside), open the Dashboard page (`/dashboard/`) in a browser and note how long the list takes to appear.
2. Add 500 more locations, each with 3 reviews, so the system holds 503 locations.
3. Open the Dashboard page again and note how long the list takes to appear.
4. Compare the two times.

## Expected result

The list appears in under 2 seconds however many locations exist.

## Actual result

- On production, with about 500 locations (3 to 4 reviews each, about 1,800 reviews), the page stays white for about 25 seconds on every visit, then the whole list appears at once.
- On the dev environment the page opens in about 0.1 second with 3 locations and still about 0.1 second with 503, so the delay cannot be seen there.
- The page does one extra data lookup for every location (4 lookups for 3 locations, 504 for 503). On production, where each lookup takes longer, this adds up.

## Environment

Seen by the reporter on production, in Chrome on a laptop with office Wi-Fi. The lookup count was measured on the dev environment.

## Attachments

Screen recording from the reporter: white page for about 25 seconds, then the whole list appears.
