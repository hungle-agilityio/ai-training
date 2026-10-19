"""Tests of the sharing gate and of the hook that enforces it.

Run: uv run pytest .claude/skills/share-report/tests --no-cov -q
"""

import json
import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

SKILL = Path(__file__).resolve().parents[1]
HOOK = SKILL.parents[1] / "hooks" / "before-artifact-publish.py"


def load(path: Path, name: str) -> ModuleType:
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = load(SKILL / "share_gate.py", "share_gate")
HOOK_MODULE = load(HOOK, "artifact_hook")


@pytest.fixture
def report(tmp_path: Path) -> Path:
    folder = tmp_path / "out" / "verify" / "20261019-000000"
    folder.mkdir(parents=True)
    (folder / "report.html").write_text("<html></html>")
    (folder / "report.json").write_text(
        json.dumps({"verdict": "PASS", "masking": {"status": "clean"}})
    )
    return folder


@pytest.fixture
def rules(tmp_path: Path) -> Path:
    path = tmp_path / "rules.md"
    path.write_text("# rules\n\n- standing-approval: on\n- max-size-mb: 15\n")
    return path


def set_masking(folder: Path, status: str | None) -> None:
    data = json.loads((folder / "report.json").read_text())
    if status is None:
        data.pop("masking", None)
    else:
        data["masking"] = {"status": status}
    (folder / "report.json").write_text(json.dumps(data))


def test_a_clean_masked_report_may_be_shared(report: Path, rules: Path) -> None:
    allowed, reason = GATE.decide(report, rules)

    assert allowed and "ALLOWED" in reason.upper()


@pytest.mark.parametrize("status", [None, "not run", "findings", "unknown"])
def test_nothing_is_shared_unless_masking_is_clean(
    report: Path, rules: Path, status: str | None
) -> None:
    set_masking(report, status)

    allowed, reason = GATE.decide(report, rules)

    assert not allowed and "masking" in reason


def test_nothing_is_shared_when_the_standing_approval_is_off(report: Path, rules: Path) -> None:
    rules.write_text("- standing-approval: off\n- max-size-mb: 15\n")

    allowed, reason = GATE.decide(report, rules)

    assert not allowed and "approval" in reason


def test_nothing_is_shared_when_the_rules_are_missing_or_unreadable(
    report: Path, tmp_path: Path
) -> None:
    assert not GATE.decide(report, tmp_path / "nope.md")[0]
    broken = tmp_path / "broken.md"
    broken.write_text("nothing useful")
    assert not GATE.decide(report, broken)[0]


def test_nothing_is_shared_when_the_page_is_too_big(report: Path, rules: Path) -> None:
    rules.write_text("- standing-approval: on\n- max-size-mb: 0.000001\n")

    allowed, reason = GATE.decide(report, rules)

    assert not allowed and "big" in reason


def test_nothing_is_shared_without_a_report_json_or_page(report: Path, rules: Path) -> None:
    (report / "report.json").unlink()
    assert not GATE.decide(report, rules)[0]


def hook(file_path: Path, project: Path, tool: str = "Artifact", action: str | None = None) -> int:
    tool_input: dict[str, str] = {"file_path": str(file_path)}
    if action:
        tool_input["action"] = action
    payload = {"tool_name": tool, "cwd": str(project), "tool_input": tool_input}
    done = subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        env={"SHARE_RULES_FILE": str(project / "rules.md")},
    )
    return done.returncode


def test_the_hook_blocks_a_report_that_is_not_masked(
    report: Path, rules: Path, tmp_path: Path
) -> None:
    set_masking(report, "not run")

    assert hook(report / "report.html", tmp_path) == 2


def test_the_hook_lets_a_masked_report_through(report: Path, rules: Path, tmp_path: Path) -> None:
    assert hook(report / "report.html", tmp_path) == 0


def test_the_hook_blocks_a_report_folder_without_its_json(
    report: Path, rules: Path, tmp_path: Path
) -> None:
    (report / "report.json").unlink()

    assert hook(report / "report.html", tmp_path) == 2


def test_the_hook_ignores_other_artifacts_other_tools_and_other_actions(
    report: Path, rules: Path, tmp_path: Path
) -> None:
    other = tmp_path / "notes.html"
    other.write_text("<html></html>")
    set_masking(report, "findings")

    assert hook(other, tmp_path) == 0
    assert hook(report / "report.html", tmp_path, tool="Read") == 0
    assert hook(report / "report.html", tmp_path, action="list") == 0
    assert hook(report / "report.html", tmp_path, action="publish") == 2


def test_the_hook_ignores_bad_input() -> None:
    done = subprocess.run(
        [sys.executable, "-I", str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        check=False,
    )

    assert done.returncode == 0


def test_the_hook_writes_one_audit_line_per_publish_call(
    report: Path, rules: Path, tmp_path: Path
) -> None:
    set_masking(report, "findings")
    hook(report / "report.html", tmp_path)

    log = (tmp_path / "out" / "artifact-publish.log").read_text().strip().splitlines()

    assert len(log) == 1 and " blocked " in log[0] and "report.html" in log[0]


def test_the_share_page_counts_for_the_size_limit_too(report: Path, rules: Path) -> None:
    (report / "report-share.html").write_text("x" * 2000)
    rules.write_text("- standing-approval: on\n- max-size-mb: 0.001\n")

    allowed, reason = GATE.decide(report, rules)

    assert not allowed and "big" in reason
