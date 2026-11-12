"""ops/release.py runs the security checks and shows them in the plan (AC6, AC7).

Each test replaces release.run_security itself: no real uv, uvx or network.
Run: uv run pytest -q --no-cov ops/tests/test_release_security.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import release, security_check
from ops.tests.test_release import CLOSING_NOW, git, merge_pr, remote_refs, repo  # noqa: F401

OK = (
    security_check.CheckResult("deploy settings", True, ()),
    security_check.CheckResult("dependencies", True, ()),
    security_check.CheckResult("secrets", True, ()),
)
FAILED_SECRETS = (
    security_check.CheckResult("deploy settings", True, ()),
    security_check.CheckResult("dependencies", True, ()),
    security_check.CheckResult("secrets", False, ("reviews/token_sample.py:3",)),
)


def run_main(clone: Path, monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    """Call release.main with green Checks; the test sets release.run_security itself."""
    monkeypatch.setattr(release, "latest_checks", lambda sha, cwd: "success")
    return release.main(list(args), cwd=clone, now=CLOSING_NOW)


def first_release(clone: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Release one pull request with no check and return the commit now on deploy."""
    monkeypatch.setattr(release, "run_security", lambda sha, since, cwd: ())
    head = merge_pr(clone, 7, "Add the filter")
    assert run_main(clone, monkeypatch) == 0
    return head


# M19 (AC7)


def test_dry_run_with_all_checks_ok_prints_security_lines_before_the_pull_requests(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    deployed = first_release(clone, monkeypatch)
    head = merge_pr(clone, 8, "Fix the score")
    capsys.readouterr()
    seen: list[tuple[str, str | None, Path]] = []

    def stand_in(sha: str, since: str | None, cwd: Path) -> tuple[security_check.CheckResult, ...]:
        seen.append((sha, since, cwd))
        return OK

    monkeypatch.setattr(release, "run_security", stand_in)
    assert run_main(clone, monkeypatch, "--dry-run") == 0
    assert seen == [(head, deployed, clone)]
    lines = capsys.readouterr().out.splitlines()
    start = lines.index("Security checks:")
    assert lines[start + 1 : start + 4] == [
        "  deploy settings: ok",
        "  dependencies: ok",
        "  secrets: ok",
    ]
    assert lines[start + 4] == f"Security review diff: {deployed[:7]}..{head[:7]}"
    assert lines[start - 1].startswith("Tag: ")
    assert start + 4 < lines.index("Client-facing pull requests:")
    assert lines[-1] == "  #8 Fix the score"


def test_an_ok_check_prints_its_lines_indented_by_four_spaces(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    first_release(clone, monkeypatch)
    merge_pr(clone, 8, "Fix the score")
    capsys.readouterr()
    skipped = (security_check.CheckResult("dependencies", True, ("skipped: no uv.lock",)),)
    monkeypatch.setattr(release, "run_security", lambda sha, since, cwd: skipped)
    assert run_main(clone, monkeypatch, "--dry-run") == 0
    lines = capsys.readouterr().out.splitlines()
    at = lines.index("  dependencies: ok")
    assert lines[at + 1] == "    skipped: no uv.lock"


def test_a_plan_built_without_security_keeps_working_with_an_empty_default() -> None:
    plan = release.Plan(
        sha="a" * 40, title="t", branch="b", tag="v1", client_facing=(), internal=()
    )
    assert plan.security == ()


# M20 (AC6)


def test_a_failed_secrets_check_refuses_the_dry_run_and_names_the_check(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    origin, clone = repo
    merge_pr(clone, 7, "Add the filter")
    before = remote_refs(origin)
    monkeypatch.setattr(release, "run_security", lambda sha, since, cwd: FAILED_SECRETS)
    assert run_main(clone, monkeypatch, "--dry-run") == 1
    err = capsys.readouterr().err
    assert "Security checks:" in err
    assert "  secrets: FAILED" in err
    assert "    reviews/token_sample.py:3" in err
    assert "security check failed: secrets" in err
    assert remote_refs(origin) == before


def test_a_failed_secrets_check_refuses_a_real_run_and_tags_and_pushes_nothing(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    origin, clone = repo
    merge_pr(clone, 7, "Add the filter")
    before = remote_refs(origin)
    monkeypatch.setattr(release, "run_security", lambda sha, since, cwd: FAILED_SECRETS)
    assert run_main(clone, monkeypatch) == 1
    err = capsys.readouterr().err
    assert "security check failed: secrets" in err
    assert remote_refs(origin) == before
    assert git(clone, "tag", "-l") == ""


def test_several_failed_checks_are_named_in_check_order(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "Add the filter")
    bad = (
        security_check.CheckResult("deploy settings", False, ("could not run: TimeoutExpired",)),
        security_check.CheckResult("dependencies", True, ()),
        security_check.CheckResult("secrets", False, ("a.py:1",)),
    )
    monkeypatch.setattr(release, "run_security", lambda sha, since, cwd: bad)
    assert run_main(clone, monkeypatch, "--dry-run") == 1
    assert "security check failed: deploy settings, secrets" in capsys.readouterr().err


def test_the_security_checks_run_after_the_ci_checks_and_before_anything_else_is_refused(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "Add the filter")
    calls: list[str] = []

    def stand_in(sha: str, since: str | None, cwd: Path) -> tuple[security_check.CheckResult, ...]:
        calls.append(sha)
        return OK

    monkeypatch.setattr(release, "run_security", stand_in)
    monkeypatch.setattr(release, "latest_checks", lambda sha, cwd: "failure")
    assert release.main(["--dry-run"], cwd=clone, now=CLOSING_NOW) == 1
    assert calls == []
    assert "did not succeed" in capsys.readouterr().err


# M21 (AC7)


def test_the_first_release_passes_no_since_and_prints_first_release_diff_line(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    head = merge_pr(clone, 7, "Add the filter")
    seen: list[tuple[str, str | None, Path]] = []

    def stand_in(sha: str, since: str | None, cwd: Path) -> tuple[security_check.CheckResult, ...]:
        seen.append((sha, since, cwd))
        return OK

    monkeypatch.setattr(release, "run_security", stand_in)
    assert run_main(clone, monkeypatch, "--dry-run") == 0
    assert seen == [(head, None, clone)]
    out = capsys.readouterr().out
    assert f"Security review diff: {head[:7]} (first release)" in out.splitlines()
    assert ".." not in out.split("Security review diff:")[1].splitlines()[0]
