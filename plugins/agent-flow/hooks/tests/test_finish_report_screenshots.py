"""A republished report in a pull request round is built at HEAD, with screenshots for needs-ui.

Run: uv run pytest ../plugins/agent-flow/hooks/tests --no-cov -q (from the app folder)
"""

import json
from importlib import util
from pathlib import Path
from types import ModuleType

HOOKS = Path(__file__).resolve().parents[1]
START = "1111111111111111111111111111111111111111"
NEW = "2222222aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
LINK = "https://claude.ai/artifact/AbC123"
PAGE = "out/verify/x/report-share.html"


def load(name: str) -> ModuleType:
    spec = util.spec_from_file_location(name.replace("-", "_") + "_shots", HOOKS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FINISH = load("before-finish-check")


def head_is(sha: str) -> "FINISH.Runner":
    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        return (0, sha + "\n") if args[:2] == ["git", "rev-parse"] else (0, "")

    return run


def setup(project: Path, *, ui: bool, commit: str | None, shots: list[str]) -> None:
    out = project / "out"
    out.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {"pr": 275, "head": START}
    if ui:
        data["ui"] = True
    (out / "pr-round.json").write_text(json.dumps(data))
    line = f"2026-11-06T13:00:00 allowed file_path={PAGE} url={LINK}"
    (out / "artifact-publish.log").write_text(line + "\n")
    if commit is not None:
        folder = project / PAGE
        folder.parent.mkdir(parents=True, exist_ok=True)
        report = {"commit": commit, "screenshots": shots}
        (folder.parent / "report.json").write_text(json.dumps(report))


def test_needs_ui_report_at_head_with_screenshots_lets_the_round_stop(tmp_path: Path) -> None:
    setup(tmp_path, ui=True, commit=NEW[:7], shots=["browser/01.png"])
    assert FINISH.report_problems(tmp_path, head_is(NEW)) == []


def test_needs_ui_report_without_screenshots_blocks_the_stop(tmp_path: Path) -> None:
    setup(tmp_path, ui=True, commit=NEW[:7], shots=[])
    problems = FINISH.report_problems(tmp_path, head_is(NEW))
    assert len(problems) == 1
    assert "no screenshots" in problems[0]
    assert "--browser --spec" in problems[0]


def test_a_report_built_at_an_older_commit_blocks_the_stop(tmp_path: Path) -> None:
    setup(tmp_path, ui=True, commit="60c1754", shots=["browser/01.png"])
    problems = FINISH.report_problems(tmp_path, head_is(NEW))
    assert len(problems) == 1
    assert "60c1754" in problems[0]
    assert "2222222" in problems[0]


def test_an_old_report_blocks_the_stop_without_needs_ui_too(tmp_path: Path) -> None:
    setup(tmp_path, ui=False, commit="60c1754", shots=[])
    assert len(FINISH.report_problems(tmp_path, head_is(NEW))) == 1


def test_needs_ui_page_with_no_report_beside_it_blocks_the_stop(tmp_path: Path) -> None:
    setup(tmp_path, ui=True, commit=None, shots=[])
    problems = FINISH.report_problems(tmp_path, head_is(NEW))
    assert len(problems) == 1
    assert "no report.json" in problems[0]


def test_the_last_publish_is_the_one_checked(tmp_path: Path) -> None:
    setup(tmp_path, ui=True, commit=NEW[:7], shots=["browser/01.png"])
    log = tmp_path / "out" / "artifact-publish.log"
    old = f"2026-11-06T12:00:00 allowed file_path=out/verify/old/report-share.html url={LINK}"
    log.write_text(old + "\n" + log.read_text())
    assert FINISH.report_problems(tmp_path, head_is(NEW)) == []
