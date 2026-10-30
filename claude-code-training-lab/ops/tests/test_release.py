"""ops/release.py cuts a sprint release without force. Run: pytest ops/tests/test_release.py"""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ops import release

GREEN = "success"
CLOSING_NOW = datetime(2026, 10, 30, 18, 30, tzinfo=UTC)  # 01:30 on the 31st in Vietnam


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=T", "-c", "user.email=t@example.com", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    )
    return done.stdout.strip()


def merge_pr(clone: Path, number: int, title: str) -> str:
    git(clone, "switch", "-c", f"feat/{number}")
    (clone / f"f{number}.txt").write_text(title)
    git(clone, "add", ".")
    git(clone, "commit", "-m", f"work {number}")
    git(clone, "switch", "main")
    git(clone, "merge", "--no-ff", f"feat/{number}", "-m",
        f"Merge pull request #{number} from owner/feat/{number}", "-m", title)
    git(clone, "push", "origin", "main")
    return git(clone, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, Path]:
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(origin))
    clone = tmp_path / "clone"
    git(tmp_path, "clone", str(origin), str(clone))
    git(clone, "switch", "-c", "main")
    (clone / "a.txt").write_text("a")
    git(clone, "add", ".")
    git(clone, "commit", "-m", "start")
    git(clone, "push", "-u", "origin", "main")
    return origin, clone


def run(clone: Path, monkeypatch: pytest.MonkeyPatch, *args: str,
        checks: str | None = GREEN) -> int:
    monkeypatch.setattr(release, "latest_checks", lambda sha, cwd: checks)
    return release.main(list(args), cwd=clone, now=CLOSING_NOW)


def remote_refs(origin: Path) -> set[str]:
    return set(git(origin, "for-each-ref", "--format=%(refname)").splitlines())


def test_dry_run_prints_plan_and_pushes_nothing(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    origin, clone = repo
    head = merge_pr(clone, 7, "Add the filter")
    before = remote_refs(origin)
    assert run(clone, monkeypatch, "--dry-run") == 0
    out = capsys.readouterr().out
    assert head[:7] in out
    assert "release/sprint-1" in out
    assert "v2026.10.31" in out
    assert "#7 Add the filter" in out
    assert remote_refs(origin) == before


def test_first_release_creates_branch_tag_and_deploy(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    origin, clone = repo
    head = merge_pr(clone, 7, "Add the filter")
    assert run(clone, monkeypatch) == 0
    assert git(origin, "rev-parse", "release/sprint-1") == head
    assert git(origin, "rev-parse", "deploy") == head
    assert git(origin, "cat-file", "-t", "v2026.10.31") == "tag"
    assert git(origin, "tag", "-l", "--format=%(contents)", "v2026.10.31") == "release/sprint-1"
    out = capsys.readouterr().out
    assert "release/sprint-1" in out and "v2026.10.31" in out and head[:7] in out
    assert "#7 Add the filter" in out
    assert out.strip().splitlines()[-1] == "Render deploys branch deploy after Checks pass."


def test_second_release_counts_up_and_lists_only_new_pull_requests(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    origin, clone = repo
    first = merge_pr(clone, 7, "Add the filter")
    assert run(clone, monkeypatch) == 0
    capsys.readouterr()
    head = merge_pr(clone, 8, "Fix the score")
    assert run(clone, monkeypatch) == 0
    out = capsys.readouterr().out
    assert "#8 Fix the score" in out and "#7" not in out
    assert git(origin, "rev-parse", "release/sprint-2") == head
    assert git(origin, "rev-parse", "deploy") == head
    assert git(origin, "rev-parse", "release/sprint-1") == first


def test_second_tag_on_the_same_day_gets_a_suffix(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    origin, clone = repo
    for number in (7, 8, 9):
        merge_pr(clone, number, f"Change {number}")
        assert run(clone, monkeypatch) == 0
    tags = set(git(origin, "tag", "-l").splitlines())
    assert tags == {"v2026.10.31", "v2026.10.31.2", "v2026.10.31.3"}


def test_sprint_number_is_one_more_than_the_highest(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    origin, clone = repo
    git(clone, "push", "origin", "main:refs/heads/release/sprint-4")
    git(clone, "push", "origin", "main:refs/heads/release/sprint-12")
    merge_pr(clone, 7, "One")
    assert run(clone, monkeypatch) == 0
    assert "refs/heads/release/sprint-13" in remote_refs(origin)


@pytest.mark.parametrize("checks", [None, "running", "failure"])
def test_refuses_when_checks_are_not_green(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str], checks: str | None) -> None:
    origin, clone = repo
    merge_pr(clone, 7, "One")
    before = remote_refs(origin)
    assert run(clone, monkeypatch, checks=checks) == 1
    err = capsys.readouterr().err.strip().splitlines()
    assert len(err) == 1 and "Checks" in err[0]
    assert remote_refs(origin) == before


def test_refuses_when_nothing_is_new(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    origin, clone = repo
    merge_pr(clone, 7, "One")
    run(clone, monkeypatch)
    before = remote_refs(origin)
    assert run(clone, monkeypatch) == 1
    assert "nothing new to release" in capsys.readouterr().err
    assert remote_refs(origin) == before


def test_refuses_when_deploy_is_not_an_ancestor(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    origin, clone = repo
    git(clone, "switch", "-c", "stray")
    (clone / "s.txt").write_text("s")
    git(clone, "add", ".")
    git(clone, "commit", "-m", "stray")
    git(clone, "push", "origin", "stray:refs/heads/deploy")
    git(clone, "switch", "main")
    merge_pr(clone, 7, "One")
    before = remote_refs(origin)
    assert run(clone, monkeypatch) == 1
    assert "not an ancestor" in capsys.readouterr().err
    assert remote_refs(origin) == before


def test_push_is_one_atomic_call_without_force(
        repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    pushes: list[list[str]] = []
    real = release.git

    def spy(args: Sequence[str], cwd: Path, check: bool = True) -> str:
        if args[0] == "push":
            pushes.append(list(args))
        return real(args, cwd, check)

    monkeypatch.setattr(release, "git", spy)
    assert run(clone, monkeypatch) == 0
    assert len(pushes) == 1
    push = pushes[0]
    assert "--atomic" in push
    assert not any(a.startswith(("--force", "--delete", "+", "-f")) for a in push)
    assert not any(a.endswith(":refs/heads/main") or a == "main" for a in push[1:])
