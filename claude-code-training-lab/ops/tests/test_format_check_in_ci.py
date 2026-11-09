"""The project stays formatted, so a build's formatter never touches files of other tasks."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_the_checks_fail_on_an_unformatted_file() -> None:
    assert (
        "run: uv run ruff format --check ."
        in (ROOT / ".github" / "workflows" / "checks.yml").read_text()
    )


def test_work_queue_formats_only_the_files_of_its_own_change() -> None:
    text = (ROOT / "plugins" / "agent-flow" / "skills" / "work-queue" / "SKILL.md").read_text()

    assert "Format only the files you changed" in text
