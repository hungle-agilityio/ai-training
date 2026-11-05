# [TASK] \<title>

- **Requester:** \<name, role>
- **Reported on:** \<YYYY-MM-DD>
- **Type:** Task
- **Labels:** `task`, `<area>`, `<high-priority, only if urgent>`, `<needs-info, remove when ready>`, `deadline: <date, only if there is one>`

## Summary

\<the work and the reason for it, in plain words; say which page, report, data or system it touches, or "nothing visible to users">

## Scope

- **Included:** \<what is part of the work>
- **Not included:** \<what is explicitly out of scope>

## Done when

Each item must be something a person can check without technical help.
- [ ] \<observable result, with exact value, page or text>
- [ ] \<observable result>

## Steps to check the result

1. \<user action, with the real names and numbers if specific data must exist>
2. \<user action>

## Screens to capture

Only when users see the change (label `needs-ui`); leave the section out otherwise. One `json` block that the build copies unchanged into the browser check: every step has a `goto` page and a `capture` selector for the part that changes (the report shows the full page next to that close-up). Optional: `actions`, `expect`, `absent`, and `"sign_in": false` on the object for the sign-in page.

```json
{"steps": [{"name": "reviews-filters", "goto": "/reviews/",
            "capture": "#filter-rating", "expect": ["Every customer review"]}]}
```

## Expected result

\<exact result>

## Environment

\<dev / staging / production>

## Attachments

\<examples, files, screenshots, or what is still to be added>
