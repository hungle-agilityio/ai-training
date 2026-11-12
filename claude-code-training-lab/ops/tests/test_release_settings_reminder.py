"""ops/release.py says when the Project settings text changed (specs/settings-paste-reminder, #552).

Git object paths count from the repository root, so the fixtures put the file under the app
folder of the flow config, as ops/tests/test_release_client_facing.py does. No network.
Run: uv run pytest -q --no-cov ops/tests/test_release_settings_reminder.py
"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from ops import release
from ops.tests.test_release import merge_pr, remote_refs, repo, run  # noqa: F401
from ops.tests.test_release_client_facing import merge_pr_file

SETTINGS = ".claude/project-instructions.md"
LINE = (
    "Project settings: .claude/project-instructions.md changed since the last release; "
    "paste it into Project settings."
)
README = Path(release.__file__).parent / "README.md"


def released(clone: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert run(clone, monkeypatch) == 0


# M1 (AC1)


def test_dry_run_ends_with_the_line_when_the_file_changed_since_the_last_release(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr_file(clone, 7, "rules one", SETTINGS)
    released(clone, monkeypatch)
    merge_pr_file(clone, 8, "rules two", SETTINGS)
    capsys.readouterr()
    assert run(clone, monkeypatch, "--dry-run") == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1] == LINE
    assert lines[-2].startswith("  ")
    assert "Internal pull requests:" in lines


# M2 (AC1)


def test_real_release_prints_the_line_after_the_groups_and_before_the_deploy_line(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr_file(clone, 7, "rules one", SETTINGS)
    released(clone, monkeypatch)
    merge_pr_file(clone, 8, "rules two", SETTINGS)
    capsys.readouterr()
    assert run(clone, monkeypatch) == 0
    lines = capsys.readouterr().out.splitlines()
    assert release.DEPLOY_LINE
    assert lines[-1] == release.DEPLOY_LINE
    assert lines[-2] == LINE
    assert lines.index("Internal pull requests:") < lines.index(LINE)


# M3 (AC2)


def test_no_line_when_the_file_is_unchanged_since_the_last_release(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr_file(clone, 7, "rules one", SETTINGS)
    released(clone, monkeypatch)
    merge_pr(clone, 8, "Other work")
    capsys.readouterr()
    assert run(clone, monkeypatch, "--dry-run") == 0
    assert run(clone, monkeypatch) == 0
    assert "Project settings:" not in capsys.readouterr().out


def test_no_line_when_the_file_is_missing_on_the_released_commit(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    assert run(clone, monkeypatch, "--dry-run") == 0
    released(clone, monkeypatch)
    merge_pr(clone, 8, "Two")
    assert run(clone, monkeypatch) == 0
    assert "Project settings:" not in capsys.readouterr().out


# M4 (AC3)


def test_first_release_prints_the_line_when_the_file_exists(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr_file(clone, 7, "rules one", SETTINGS)
    assert run(clone, monkeypatch, "--dry-run") == 0
    assert capsys.readouterr().out.splitlines()[-1] == LINE


def test_a_file_new_since_the_last_release_counts_as_changed(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    released(clone, monkeypatch)
    merge_pr_file(clone, 8, "rules one", SETTINGS)
    capsys.readouterr()
    assert run(clone, monkeypatch, "--dry-run") == 0
    assert capsys.readouterr().out.splitlines()[-1] == LINE


# M5 (AC4)


def test_a_failing_check_prints_no_line_and_keeps_the_exit_code(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    origin, clone = repo
    merge_pr_file(clone, 7, "rules one", SETTINGS)
    real = release.git

    def broken(args: Sequence[str], cwd: Path, check: bool = True) -> str:
        if args[0] == "ls-tree":
            raise subprocess.CalledProcessError(128, ["git", *args], stderr="fatal: bad object")
        return real(args, cwd, check)

    monkeypatch.setattr(release, "git", broken)
    assert run(clone, monkeypatch, "--dry-run") == 0
    assert run(clone, monkeypatch) == 0
    captured = capsys.readouterr()
    assert "Project settings:" not in captured.out
    assert captured.err == ""
    assert "refs/heads/deploy" in remote_refs(origin)


def test_the_check_reads_git_objects_not_the_working_tree(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ops import flow_config

    _, clone = repo
    merge_pr_file(clone, 7, "rules one", SETTINGS)
    released(clone, monkeypatch)
    merge_pr(clone, 8, "Other work")
    (clone / flow_config.load().project_app_dir / SETTINGS).write_text("edited, not committed")
    capsys.readouterr()
    assert run(clone, monkeypatch, "--dry-run") == 0
    assert "Project settings:" not in capsys.readouterr().out


# M6 (AC5)


def test_a_plan_built_without_the_new_field_prints_no_line() -> None:
    plan = release.Plan(
        sha="a" * 40, title="t", branch="b", tag="v1", client_facing=(), internal=()
    )
    assert plan.settings_changed is False
    assert LINE not in release.describe(plan)


def test_readme_release_section_names_the_line() -> None:
    section = README.read_text().split("\n## Release\n", 1)[1].split("\n## ", 1)[0]
    assert "Project settings: .claude/project-instructions.md changed since the last release" in (
        section
    )
