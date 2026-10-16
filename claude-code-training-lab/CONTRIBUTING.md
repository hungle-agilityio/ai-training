# Contributing

This is a private training project. These notes say how work gets in.

## Report or ask for something

Open an issue with one of the forms (bug, new feature, task or epic). Write in plain words and say what a person does and sees. A bug needs numbered steps, the expected and the actual result.

## Make a change

1. One branch per issue, named `<kind>/<number>-<description>`, for example `bug/12-dashboard-wrong-score`.
2. Write the test first, then the code.
3. Run the checks before you push: `uv run ruff check .`, `uv run mypy .`, `uv run pytest`.
4. One pull request does one thing, into `main`. Describe what and why, how you tested it with the real output, and end with `Closes #<number>`.
5. A person reviews and merges it. Nobody pushes to `main` directly.

The full rules are in the [README](README.md) and in `.claude/rules/`.

## Secrets

Never commit `.env`, keys or real customer data. Copy `env.example` to `.env` and fill it in.

## Licence

There is no licence yet. The repository is private and all rights are reserved.
