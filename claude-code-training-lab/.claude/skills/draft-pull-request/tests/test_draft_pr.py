"""Tests of the pull request draft builder.

Run: uv run pytest .claude/skills/draft-pull-request/tests --no-cov -q
"""

import json
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1]


def load() -> ModuleType:
    spec = util.spec_from_file_location("draft_pr", SKILL / "draft_pr.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DRAFT = load()


def make_report(folder: Path, masking: str = "clean", share: str | None = None) -> Path:
    folder.mkdir(parents=True)
    report: dict[str, Any] = {
        "title": "Reviews filters",
        "verdict": "PASS",
        "masking": {"status": masking},
        "share": {"url": share, "date": "2026-10-19"} if share else None,
        "axes": [
            {"name": "Lint", "status": "PASS", "evidence": "All checks passed!"},
            {"name": "Tests", "status": "PASS", "evidence": "142 passed, 0 failed, coverage 99%"},
        ],
    }
    (folder / "report.json").write_text(json.dumps(report))
    return folder


def make_compare(folder: Path, masking: str = "clean") -> Path:
    (folder / "before").mkdir(parents=True)
    (folder / "after").mkdir()
    pairs = []
    for name, label in (("reviews", "changed"), ("dashboard", "no visible difference")):
        (folder / "before" / f"{name}.png").write_bytes(b"before-" + name.encode())
        (folder / "after" / f"{name}.png").write_bytes(b"after-" + name.encode())
        pairs.append(
            {
                "name": name,
                "label": label,
                "before": str(folder / "before" / f"{name}.png"),
                "after": str(folder / "after" / f"{name}.png"),
                "url": f"/{name}/",
            }
        )
    (folder / "compare.json").write_text(
        json.dumps({"base": "abc", "head": "def", "pairs": pairs, "masking": {"status": masking}})
    )
    return folder


def draft(tmp_path: Path, **over: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "title": "[FEAT] Reviews page filters",
        "what": "The reviews page can be filtered by location, rating and week.",
        "why": "Managers need to see one week or one rating at a time.",
        "issue": 12,
        "report": make_report(tmp_path / "report", share="https://claude.ai/artifact/x"),
        "compare": make_compare(tmp_path / "compare"),
        "no_visual": False,
        "out": tmp_path / "out",
    }
    args.update(over)
    result: dict[str, Any] = DRAFT.build_draft(**args)
    return result


def test_a_full_draft_has_every_section_the_real_numbers_and_closes(tmp_path: Path) -> None:
    result = draft(tmp_path)
    body = (tmp_path / "out" / "pr-body.md").read_text()

    assert result["complete"] and result["ready_to_create"] and result["problems"] == []
    for heading in ("## What", "## Why", "## How tested", "## Evidence", "## One concern"):
        assert heading in body
    assert "142 passed, 0 failed, coverage 99%" in body
    assert "https://claude.ai/artifact/x" in body
    assert body.rstrip().endswith("Closes #12")


def test_the_images_are_copied_to_a_folder_to_drag_in_and_the_unchanged_ones_are_skipped(
    tmp_path: Path,
) -> None:
    result = draft(tmp_path)
    images = sorted(p.name for p in (tmp_path / "out" / "images").iterdir())

    assert images == ["01-reviews-after.png", "01-reviews-before.png"]
    assert len(result["images"]) == 2
    assert "01-reviews-before.png" in (tmp_path / "out" / "pr-body.md").read_text()


def test_without_an_issue_number_the_draft_is_complete_but_not_ready(tmp_path: Path) -> None:
    result = draft(tmp_path, issue=None)
    body = (tmp_path / "out" / "pr-body.md").read_text()

    assert result["complete"] and not result["ready_to_create"]
    assert "Closes #" not in body
    assert "no issue number yet" in body.lower()


def test_images_that_are_not_masked_are_refused(tmp_path: Path) -> None:
    result = draft(tmp_path, compare=make_compare(tmp_path / "bad", masking="findings"))

    assert not result["complete"]
    assert any("masking" in line for line in result["problems"])
    assert not (tmp_path / "out" / "images").exists() or not list(
        (tmp_path / "out" / "images").iterdir()
    )


def test_evidence_is_required_unless_the_change_is_not_visible(tmp_path: Path) -> None:
    missing = draft(tmp_path, compare=None)
    invisible = draft(tmp_path / "second", compare=None, no_visual=True)

    assert any("evidence" in line for line in missing["problems"])
    assert invisible["complete"]
    assert (
        "nothing visible to users"
        in (tmp_path / "second" / "out" / "pr-body.md").read_text().lower()
    )


def test_how_tested_needs_a_report(tmp_path: Path) -> None:
    result = draft(tmp_path, report=None)

    assert not result["complete"]
    assert any("how tested" in line for line in result["problems"])


def test_a_report_that_is_not_shared_is_named_as_local_only(tmp_path: Path) -> None:
    draft(tmp_path, report=make_report(tmp_path / "local"))

    body = (tmp_path / "out" / "pr-body.md").read_text()
    assert "not shared" in body


@pytest.mark.parametrize("field", ["what", "why"])
def test_empty_what_or_why_is_refused(tmp_path: Path, field: str) -> None:
    result = draft(tmp_path, **{field: "  "})

    assert any(field in line.lower() for line in result["problems"])


def test_the_title_must_start_with_a_known_type(tmp_path: Path) -> None:
    assert any("title" in line for line in draft(tmp_path, title="Reviews filters")["problems"])


def test_a_failing_report_is_still_described_honestly(tmp_path: Path) -> None:
    folder = tmp_path / "failing"
    folder.mkdir()
    (folder / "report.json").write_text(
        json.dumps(
            {
                "verdict": "FAIL",
                "masking": {"status": "clean"},
                "share": None,
                "axes": [{"name": "Tests", "status": "FAIL", "evidence": "1 failed"}],
            }
        )
    )

    result = draft(tmp_path, report=folder)

    assert "FAIL" in (tmp_path / "out" / "pr-body.md").read_text()
    assert any("verdict" in line for line in result["problems"])


def test_draft_json_is_written_next_to_the_body(tmp_path: Path) -> None:
    result = draft(tmp_path)

    saved = json.loads((tmp_path / "out" / "draft.json").read_text())

    assert saved["ready_to_create"] == result["ready_to_create"] and saved["images"]
