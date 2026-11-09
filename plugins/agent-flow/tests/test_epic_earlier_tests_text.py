"""A task of an epic may change a test from an earlier task of the epic (ADR-022)."""

from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
WORK_QUEUE = (PLUGIN / "skills" / "work-queue" / "SKILL.md").read_text()


def test_work_queue_defines_a_test_from_an_earlier_task_of_the_epic() -> None:
    assert "not on `origin/main` came from an earlier task of the same epic" in WORK_QUEUE


def test_work_queue_asks_to_say_which_test_changed() -> None:
    assert "which test changed, how, and for which AC" in WORK_QUEUE
