---
name: check-in-browser
description: Start the app on a throw-away demo database, drive the pages in a headless browser, save a screenshot of each step and report console errors, failed requests and missing text. Use in /verify for any issue that changes what users see, or when the user asks to check a page in the browser.
---

# Check in a browser

Unit tests prove the parts; the browser proves the feature. This skill runs the real pages the way a user would and reports what a user cannot see: console errors and failed requests.

## Run it

```
uv run python .claude/skills/check-in-browser/browser_check.py
```

- It starts the app on a **throw-away demo database** (never `db.sqlite3`), runs the steps in a headless Chromium with a fixed window size (1280 by 800), and stops the app and deletes the database at the end.
- Default steps: the dashboard, the reviews page, the Bad and Good filters, and a filter with no match.
- Screenshots, one per step, and `result.json` go to `out/browser-check/<time>/` (git-ignored). The screenshots show demo data only.
- For another page or flow, write a spec from the issue's "Steps to check the result" and pass it with `--spec`: a list of steps, each with a `name`, a `goto` address, optional `actions` (`select`, `fill`, `click` on a selector), and optional `expect` and `absent` texts. A step may also give `status`, the HTTP status its page must answer (for example 404 for an error page). A spec written as an object (`{"steps": [...]}`) may set `"debug": false` to run the app as in production (needed to see `404.html` or `500.html`) and `"viewport": "390x844"` for a narrow screen; `--debug-off` and `--viewport` do the same on the command line and win over the spec.

```
{"steps": [{"name": "week-filter", "goto": "/reviews/",
            "actions": [{"fill": {"#filter-week": "2026-10-12"}}, {"click": "button[type=submit]"}],
            "expect": ["Week:"]}]}
```

## Read the result

| Exit code | Meaning | What to report |
|---|---|---|
| 0 | `result: clean`: no console error, no failed request, every expected text shown | PASS, with the screenshots of the steps |
| 1 | Something is wrong | FAIL, with each flagged line and its screenshot |
| 3 | **Masking:** personal data was found; the run stopped and kept no screenshot of that step | FAIL for masking: name the kind and the step (never the value), and do not share anything |
| 2 | The check could not run | NOT CONFIGURED and the reason; if no browser is installed run `uv sync` and `uv run playwright install chromium`, then try once more |

## Masking

Every page text, log line and address is scanned for emails, phone numbers, tokens, local paths, public IP addresses and credentials in a URL. The first finding stops the whole run, the screenshot of that step is deleted, and logs are stored with the values replaced by `[redacted]`; only the kind and the step are reported. `result.json` carries `masking: clean` or `findings`, which the report and the sharing gate read.

- Only the page is captured (never the browser window), on a throw-away demo database.
- Fields that show customer text, names or emails are marked `data-sensitive` in the templates; `--blur` blurs them in the screenshots.
- `--plant "<text>"` adds a review with that text to the throw-away database, to prove that the scan stops a run (for example a fake email). Use it only for that test.

## Rules

- After **three failed actions in a row** the run stops by itself. Do not retry in a loop: tell the user what failed and ask.
- Never point it at the developer database or at real customer data; never publish the screenshots (sharing is a separate step with its own checks).
- The browser extension for Chrome is not needed and is not used; this check has its own browser and profile.
- Report only what the output says. Never write PASS without having run it.
