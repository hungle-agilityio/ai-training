"""A pull request round that pushes commits must republish its verify report before it stops.

Run: uv run pytest ../plugins/agent-flow/hooks/tests --no-cov -q (from the app folder)
"""

import json
from importlib import util
from pathlib import Path
from types import ModuleType

HOOKS = Path(__file__).resolve().parents[1]
START = "1111111111111111111111111111111111111111"
NEW = "2222222222222222222222222222222222222222"
LINK = "https://claude.ai/artifact/AbC123"


def load(name: str) -> ModuleType:
    spec = util.spec_from_file_location(name.replace("-", "_"), HOOKS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FINISH = load("before-finish-check")


def head_is(sha: str) -> "FINISH.Runner":
    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        return (0, sha + "\n") if args[:2] == ["git", "rev-parse"] else (0, "")

    return run


def round_file(project: Path, head: str = START, pr: int = 275) -> None:
    (project / "out").mkdir(parents=True, exist_ok=True)
    (project / "out" / "pr-round.json").write_text(json.dumps({"pr": pr, "head": head}))


def publish_log(project: Path, *lines: str) -> None:
    (project / "out").mkdir(parents=True, exist_ok=True)
    (project / "out" / "artifact-publish.log").write_text("\n".join(lines) + "\n")


def test_new_commits_without_a_republish_block_the_stop(tmp_path: Path) -> None:
    round_file(tmp_path)
    problems = FINISH.report_problems(tmp_path, head_is(NEW))
    assert len(problems) == 1
    assert "PR #275" in problems[0]
    assert "republish" in problems[0]


def test_a_publish_to_the_same_link_lets_the_round_stop(tmp_path: Path) -> None:
    round_file(tmp_path)
    line = f"2026-11-06T13:00:00 allowed file_path=out/verify/x/report-share.html url={LINK}"
    publish_log(tmp_path, line)
    assert FINISH.report_problems(tmp_path, head_is(NEW)) == []


def test_a_blocked_publish_or_one_without_a_link_does_not_count(tmp_path: Path) -> None:
    round_file(tmp_path)
    publish_log(
        tmp_path,
        f"2026-11-06T13:00:00 blocked file_path=out/verify/x/report-share.html url={LINK}",
        "2026-11-06T13:01:00 allowed file_path=out/verify/x/report-share.html",
    )
    assert len(FINISH.report_problems(tmp_path, head_is(NEW))) == 1


def test_a_round_with_no_new_commit_needs_no_republish(tmp_path: Path) -> None:
    round_file(tmp_path)
    assert FINISH.report_problems(tmp_path, head_is(START)) == []


def test_an_issue_build_has_no_round_file_and_is_not_checked(tmp_path: Path) -> None:
    assert FINISH.report_problems(tmp_path, head_is(NEW)) == []


def test_the_check_runs_only_in_loop_mode(tmp_path: Path) -> None:
    round_file(tmp_path)
    assert FINISH.evaluate({}, tmp_path, {}, head_is(NEW)) == []
