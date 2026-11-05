"""The skill tests run against one project: the folder pytest starts in (it holds ops/flow.toml).

The skills find the project through CLAUDE_PROJECT_DIR, as Claude Code sets it for a session.
"""

import os
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    if not (project / "ops" / "flow.toml").is_file():
        raise pytest.UsageError(
            f"run the skill tests from a project folder with ops/flow.toml, not {project}"
        )
    os.environ["CLAUDE_PROJECT_DIR"] = str(project)
