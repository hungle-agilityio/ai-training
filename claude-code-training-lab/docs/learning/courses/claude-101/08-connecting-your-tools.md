# Lesson 8: Connecting Your Tools

- **Course:** Claude 101 (lesson 8 of 13, ~15 min)
- **Source:** https://academy.claude.com/courses/claude-101/connecting-your-tools
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic.

## Setup (do once)

1. Upload `docs/app/reviewradar-project-context-2026-10.md` to your Google Drive. Do not upload anything sensitive.
2. Claude.ai > Customize > Connectors (or **+** in the chat window > Connectors) > find **Google Drive** > **Connect** > sign in and review the permissions before authorizing.
3. Test with: `Can you access my Google Drive?`

If you prefer another connector (Notion, Confluence), use it with the same file. Avoid connecting email for these exercises.

## Exercises

### Ex 1: Without vs with a connector

**Where:** Claude.ai (regular chat)

**Initial prompt** (Google Drive connector turned off):
```
Find the ReviewRadar project context file in my Google Drive and list the planned entities.
```
**Link:**

**Improved prompt** (connector turned on, new chat):
```
Find the ReviewRadar project context file in my Google Drive and list the planned entities.
```
**Link:**

### Ex 2: Vague vs specific request on a connector

**Where:** Claude.ai (regular chat, connector on)

**Initial prompt:**
```
What do my docs say about the project?
```
**Link:**

**Improved prompt** (new chat):
```
Search my Google Drive for the file "reviewradar-project-context-2026-10". From the section "Engineering standards", list the rules about testing and database queries, and quote each rule. If you cannot find the file, say so instead of guessing.
```
**Link:**

Open the Drive file and check that the quotes match exactly.

### Ex 3: Review permissions

**Where:** Claude.ai (Customize > Connectors), no chat needed

1. Open the Google Drive connector and read the permissions it has.
2. Find where you can toggle individual permissions.
3. Disconnect the connector, confirm that Ex 1's prompt no longer finds the file, then reconnect if you want to keep it.
4. Find where the same access can be revoked from the Google account's security settings.

## Key takeaways

- **Connectors** give Claude access to the tools and data you already use, so it does not start from scratch. Depending on permissions, Claude can read or act (search, create, update).
- Powered by **MCP** (Model Context Protocol), an open standard like USB-C: one consistent interface to many applications.
- Two types: **web connectors** (cloud services such as Google Drive, Notion, Slack, Asana, Jira) and **desktop extensions** (local files, browser control, native apps; installed in Settings > Extensions).
- Directory entries are per connector, not per app: look for Atlassian to reach Jira and Confluence. No entry? Add a **custom connector**.
- Set up a web connector: find it, Connect, authenticate, review permissions, authorize, then test with "Can you access my [tool]?"
- Team and Enterprise: an organization Owner must add a connector first.
- **Security:** scoped permissions you can toggle; Claude sees only what your account can see; access is revocable (Customize > Connectors or the third-party service); install custom connectors only from trusted sources.
- Name the source and the section in your request ("search my Drive for X, in section Y") and ask Claude to say so if it cannot find it.
- Claude Code uses the same MCP standard, configured per project in `.mcp.json` (Day 8 of the 15-day plan).
