# Spec: locations-settings

## Summary

A pure rule in `reviews/location_names.py` checks a location name. A new repository `reviews/location_repository.py` adds and renames locations. The Settings page gets a "Locations" panel that lists the locations and adds one; each location has its own rename page. The empty dashboard gets a link to that panel. No migration and no change to the demo data.

## Acceptance criteria

**The rule (T1)**

- **AC1.** `reviews/location_names.py` defines `clean_location_name(text)`: the text with leading and trailing spaces removed and every run of spaces inside it made one space.
- **AC2.** `location_name_errors(name, taken_names)` returns a list of error messages, empty when the name is valid: the cleaned name must be 1 to 120 characters ("Enter a name of 1 to 120 characters."); a cleaned name equal to one of `taken_names` ignoring case gives "A location with this name already exists."
- **AC3.** The rule has no database access and no Django model import.

**Storing locations (T2)**

- **AC4.** `reviews/location_repository.py`, the only place that writes locations: add a location with a name to the business with the lowest id, creating a business named "My business" first when there is none, and return its id; rename a location (only its name changes: reviews, goal and score stay); get one location's id and name by id (None when missing); list the names of all locations except a given id, in one query.
- **AC5.** No migration; `Branch` and `Business` do not change.

**Settings panel (T3)**

- **AC6.** `/settings/` shows `<section class="panel settings-panel" id="settings-locations">` titled "Locations", after Account and before Location goals. It lists every location ordered by name then id, one row each: the name (`data-sensitive` is not needed: it is not customer data) and a link "Rename" to `/settings/locations/<id>/` with `aria-label="Rename <name>"`. With no locations it shows "No locations yet. Add your first one below." Below the list, an "Add a location" form: Name (text, maxlength 120) and a button "Add location".
- **AC7.** The form posts to `/settings/locations/` (POST only; GET redirects to `/settings/`). A valid post adds the location with the cleaned name (AC1) and redirects to `/settings/?locations=added#settings-locations`, where the notice "Location added." (`id="locations-saved"`, `role="status"`) shows. The new location then shows on the dashboard, in Location goals, in the Reviews location filter and on the compare page, with no score.
- **AC8.** An invalid post (AC2) saves nothing and shows `/settings/` again with the typed name kept and the error under the field, linked by `aria-describedby`; the other panels show as on a normal visit.
- **AC9.** `/settings/` runs at most 4 queries (as on `main`): the panel uses the list that Location goals already loads.

**Rename (T4)**

- **AC10.** `/settings/locations/<id>/` (GET and POST) shows "Rename location" with a Name field filled with the current name, a button "Save name" and a link "Cancel" to `/settings/#settings-locations`. An unknown id is 404.
- **AC11.** A valid post saves the cleaned name and redirects to `/settings/?locations=renamed#settings-locations` with the notice "Location renamed."; an invalid post follows AC8 (the location's own name does not count as taken, so a change of case only is allowed) and shows the rename page again. Reviews, goal and score of the location do not change.
- **AC12.** The rename page GET runs at most 3 queries, a post at most 5.

**Empty dashboard (T5)**

- **AC13.** With no locations, the dashboard empty panel "No locations yet" keeps its text and adds a link "Add a location" to `/settings/#settings-locations`.

**All tasks**

- **AC14.** `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` pass. Each task puts its new tests in the new test files it names; existing tests change only where its issue lists them under "Existing tests that change".

## Edge cases

- Empty: no locations → the panel text of AC6, the dashboard link of AC13; the first add creates "My business".
- Two locations "Downtown" and "downtown" are refused (AC2); renaming "Downtown" to "DOWNTOWN" is allowed.
- A name with `<` or `&` is escaped like any other text.
- Large data: 200 locations → the panel adds no query; the list is the one Location goals loads.
- Permissions: every signed-in user; visitors are sent to sign in for every new URL.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q12 Actions | Add and rename | Also delete | Delete would remove the location's reviews |
| Q13 Which business | The one business; "My business" created when none | Ask for the business name | One business per installation |
| Q14 Name rule | Trimmed, 1–120 characters, unique ignoring case | Required only | Two locations with one name cannot be told apart |
| Q15 UI | Panel on Settings + rename page (like Reply templates) | Rename in place | Same pattern as templates, no JavaScript |
| Q16 Settings queries | Reuse the goals list, still 4 | Allow 5 | Two tests pin Settings at 4 |
| Q17 Empty dashboard | Link "Add a location" | Unchanged | The text says to add one but not where |

## Design

Design card linked in `design/locations-settings/README.md`.

## Open questions
