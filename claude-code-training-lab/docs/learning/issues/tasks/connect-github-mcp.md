# [TASK] connect the AI assistant to the GitHub project

- **Requester:** Hung Le, project owner
- **Reported on:** 2026-10-19
- **Type:** Task
- **Labels:** `task`, `tooling`

## Summary

Let the AI assistant read the project's issues and pull requests on GitHub directly, through its official GitHub connection, instead of only through the command line. The work touches the assistant's shared project settings and the access key that GitHub gave to this project. Nothing visible to users of the ReviewRadar app changes.

The connection uses a personal access key kept only on the owner's computer, never written in any project file. The key is limited to one repository, `hungle-agilityio/ai-training`, so the assistant cannot reach any other repository.

The connection was first tried before the key included the repository, and GitHub answered that the repository could not be found. After the repository was added to the key, the same request worked.

## Scope

- **Included:** adding the GitHub connection to the shared project settings; limiting the access key to the one repository; checking that the assistant can identify the account and read the repository's issues.
- **Not included:** creating, changing or closing issues and pull requests through the connection (those still need the owner's approval, one by one); connecting any other service; changing which repository the project is allowed to reach.

## Done when

Each item must be something a person can check without technical help.
- [x] The assistant, asked who it is signed in as on GitHub, answers with the account `hungle-agilityio` (Hung Le).
- [x] The assistant, asked to list the issues of `hungle-agilityio/ai-training`, answers without an error. At the time of checking the repository had no issues, so the list is empty.
- [ ] The access key is not written anywhere in the project files or in the pull request.
- [ ] Asked to read a different repository, the assistant is refused.

## Steps to check the result

1. Open the project in the AI assistant from the `claude-code-training-lab` folder.
2. Ask: "Who am I on GitHub?" The answer names the account `hungle-agilityio`.
3. Ask: "List the issues of hungle-agilityio/ai-training." The answer is a list (empty if no issue has been published yet), not an error.
4. Ask: "List the issues of any other repository." The assistant refuses and says which rule stopped it.

## Expected result

Steps 2 and 3 answer with the account name and the issue list. Step 4 is refused. The access key never appears in an answer.

## Environment

dev

## Attachments

Nothing attached yet. To add: the answers from steps 2 to 4, as text.
