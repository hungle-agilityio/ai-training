# Generative AI with LLMs Training



## Getting started
- Update content for README.file later.

## How to run the checks

The app lives in `claude-code-training-lab/`. Run every command from that folder, with Python 3.11 or newer and [`uv`](https://docs.astral.sh/uv/) installed.

```bash
cd claude-code-training-lab
uv sync                    # install the locked dependencies
```

These are the same checks the GitHub workflow (`.github/workflows/checks.yml`) runs:

```bash
uv run ruff check .        # lint
uv run mypy .              # types (strict)
uv run pytest -q           # tests, with coverage
```

For a faster test run without coverage, use `uv run pytest -q --no-cov`.

To start the server:

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

Then open http://127.0.0.1:8000/. Demo data, the other checks (coverage gate, hook and skill tests, browser check) and more are in [`claude-code-training-lab/README.md`](claude-code-training-lab/README.md).
