"""The skill tests run against one project: the folder pytest starts in (it holds the flow.toml).

The skills find the project through CLAUDE_PROJECT_DIR, as Claude Code sets it for a session.
"""

import os
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd()).resolve()
    configs = (project / ".flow" / "flow.toml", project / "ops" / "flow.toml")
    if not any(config.is_file() for config in configs):
        raise pytest.UsageError(
            "run the skill tests from a project folder with .flow/flow.toml or ops/flow.toml, "
            f"not {project}"
        )
    os.environ["CLAUDE_PROJECT_DIR"] = str(project)
