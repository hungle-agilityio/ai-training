"""ops/release.py creates a GitHub Release page for the new tag (specs/release-page, #548).

The fixture repositories keep their local origin, so fetch and push stay local. For the GitHub
cases the fake `run` answers `git remote get-url origin` with a GitHub URL, answers `gh` itself
and passes every other call to the real `subprocess.run`. No network.
Run: uv run pytest -q --no-cov ops/tests/test_release_github_page.py
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ops import release
from ops.tests.test_release import merge_pr, remote_refs, repo, run  # noqa: F401

GITHUB_URL = "https://github.com/acme/shop.git"
PAGE_URL = "https://github.com/acme/shop/releases/tag/v2026.10.31"
NOTES_URL = "https://claude.ai/artifact/9YeTDzCKwuvkYq2jDphaye"
TAG = "v2026.10.31"
README = Path(release.__file__).parent / "README.md"

Answer = Callable[[list[str], dict[str, Any]], "subprocess.CompletedProcess[str]"]


def page_created(cmd: list[str], kwargs: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(cmd, 0, stdout="\n" + PAGE_URL + "\n\n", stderr="")


class Fake:
    """Records every call; answers the origin lookup (GitHub cases) and `gh`."""

    def __init__(self, gh: Answer = page_created, github: bool = True) -> None:
        self.real = subprocess.run
        self.gh = gh
        self.github = github
        self.calls: list[list[str]] = []
        self.gh_kwargs: list[dict[str, Any]] = []

    def __call__(self, cmd: Any, *args: Any, **kwargs: Any) -> Any:
        words = [str(word) for word in cmd]
        self.calls.append(words)
        if self.github and words[:1] == ["git"] and words[-3:] == ["remote", "get-url", "origin"]:
            return subprocess.CompletedProcess(words, 0, stdout=GITHUB_URL + "\n", stderr="")
        if words[:1] == ["gh"]:
            self.gh_kwargs.append(kwargs)
            return self.gh(words, kwargs)
        return self.real(cmd, *args, **kwargs)

    @property
    def gh_calls(self) -> list[list[str]]:
        return [call for call in self.calls if call[:1] == ["gh"]]

    def pushes_after_gh(self) -> list[list[str]]:
        first = next(i for i, call in enumerate(self.calls) if call[:1] == ["gh"])
        return [c for c in self.calls[first + 1 :] if c[:1] == ["git"] and "push" in c]


@pytest.fixture
def state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    folder = tmp_path / "state" / "nested"
    monkeypatch.setattr(release, "STATE_DIR", folder)
    return folder


def fake(monkeypatch: pytest.MonkeyPatch, gh: Answer = page_created, github: bool = True) -> Fake:
    made = Fake(gh, github)
    monkeypatch.setattr(subprocess, "run", made)
    return made


def notes(state: Path) -> Path:
    return state / ("release-" + TAG + ".md")


# M1 (AC1)


def test_notes_file_has_the_two_groups_and_the_notes_link(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, clone = repo
    sha = merge_pr(clone, 528, "spec: epic-review-checklist")
    fake(monkeypatch)
    assert run(clone, monkeypatch, "--notes-url", NOTES_URL) == 0
    assert notes(state).read_text() == (
        f"Release {TAG} (release/sprint-1, commit {sha[:7]})\n"
        "\n"
        "Client-facing pull requests:\n"
        "- (none)\n"
        "\n"
        "Internal pull requests:\n"
        "- #528 spec: epic-review-checklist\n"
        "\n"
        f"Release notes: {NOTES_URL}\n"
    )


def test_gh_release_create_runs_in_the_repository_for_the_new_tag(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    made = fake(monkeypatch)
    assert run(clone, monkeypatch, "--notes-url", NOTES_URL) == 0
    assert made.gh_calls == [
        ["gh", "release", "create", TAG, "--title", TAG]
        + ["--notes-file", str(notes(state)), "--verify-tag"]
    ]
    assert notes(state).is_absolute()
    kwargs = made.gh_kwargs[0]
    assert kwargs["cwd"] == clone
    assert kwargs["timeout"] == 60
    assert kwargs["check"] is True


# M2 (AC1)


def test_without_notes_url_the_link_and_its_blank_line_are_left_out(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    fake(monkeypatch)
    assert run(clone, monkeypatch) == 0
    text = notes(state).read_text()
    assert "Release notes" not in text
    assert text.endswith("Internal pull requests:\n- #7 One\n")


def test_notes_text_lists_each_group_and_marks_an_empty_one() -> None:
    plan = release.Plan(
        sha="5b8d883" + "0" * 33,
        title="t",
        branch="release/sprint-6",
        tag="v2026.11.12",
        client_facing=("#525 A member's claimed task holds its files in the loop",),
        internal=(),
    )
    assert release.notes_text(plan, NOTES_URL) == (
        "Release v2026.11.12 (release/sprint-6, commit 5b8d883)\n"
        "\n"
        "Client-facing pull requests:\n"
        "- #525 A member's claimed task holds its files in the loop\n"
        "\n"
        "Internal pull requests:\n"
        "- (none)\n"
        "\n"
        f"Release notes: {NOTES_URL}\n"
    )


def test_an_empty_notes_url_counts_as_not_given() -> None:
    plan = release.Plan(
        sha="a" * 40, title="t", branch="b", tag="v1", client_facing=(), internal=()
    )
    assert release.notes_text(plan, "") == release.notes_text(plan, None)
    assert "Release notes" not in release.notes_text(plan, None)


def test_an_old_notes_file_is_overwritten(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    state.mkdir(parents=True)
    notes(state).write_text("old")
    fake(monkeypatch)
    assert run(clone, monkeypatch) == 0
    assert notes(state).read_text().startswith("Release " + TAG)


# M3 (AC2)


def test_stdout_starts_with_the_release_page_and_ends_with_the_deploy_line(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    fake(monkeypatch)
    assert run(clone, monkeypatch) == 0
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "Release page: " + PAGE_URL
    assert lines[1].startswith("Commit: ")
    assert lines[-1] == release.DEPLOY_LINE
    assert captured.err == ""


def test_success_without_a_printed_url_adds_no_line_and_no_warning(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    fake(monkeypatch, gh=lambda cmd, kwargs: subprocess.CompletedProcess(cmd, 0, "", ""))
    assert run(clone, monkeypatch) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0].startswith("Commit: ")
    assert captured.err == ""


# M4 (AC3)


def gh_exit_1(cmd: list[str], kwargs: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    raise subprocess.CalledProcessError(1, cmd, output="", stderr="first\nHTTP 403: no\n\n")


def gh_exit_1_stdout_only(
    cmd: list[str], kwargs: dict[str, Any]
) -> subprocess.CompletedProcess[str]:
    raise subprocess.CalledProcessError(1, cmd, output="said on stdout\n", stderr="")


def gh_exit_2_silent(cmd: list[str], kwargs: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    raise subprocess.CalledProcessError(2, cmd, output="", stderr="")


def gh_missing(cmd: list[str], kwargs: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    raise FileNotFoundError("gh")


def gh_slow(cmd: list[str], kwargs: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    raise subprocess.TimeoutExpired(cmd, 60)


@pytest.mark.parametrize(
    ("gh", "reason"),
    [
        (gh_exit_1, "HTTP 403: no"),
        (gh_exit_1_stdout_only, "said on stdout"),
        (gh_exit_2_silent, "exit 2"),
        (gh_missing, "FileNotFoundError"),
        (gh_slow, "TimeoutExpired"),
    ],
)
def test_a_failed_page_is_a_warning_and_the_release_still_exits_0(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    gh: Answer,
    reason: str,
) -> None:
    origin, clone = repo
    merge_pr(clone, 7, "One")
    made = fake(monkeypatch, gh=gh)
    assert run(clone, monkeypatch) == 0
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0].startswith("Commit: ")
    assert lines[-1] == release.DEPLOY_LINE
    assert captured.err.splitlines() == [
        f"warning: GitHub Release not created ({reason}); run: gh release create {TAG} "
        f"--title {TAG} --notes-file {notes(state)} --verify-tag"
    ]
    assert made.pushes_after_gh() == []
    assert {"refs/heads/release/sprint-1", "refs/tags/" + TAG, "refs/heads/deploy"} <= (
        remote_refs(origin)
    )


def test_a_notes_file_that_cannot_be_written_is_the_warning_and_gh_is_not_run(
    repo: tuple[Path, Path],  # noqa: F811
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    blocker = tmp_path / "a-file"
    blocker.write_text("x")
    monkeypatch.setattr(release, "STATE_DIR", blocker / "below")
    made = fake(monkeypatch)
    assert run(clone, monkeypatch) == 0
    captured = capsys.readouterr()
    assert made.gh_calls == []
    assert captured.err.startswith("warning: GitHub Release not created (")
    assert "; run: gh release create " + TAG in captured.err
    assert captured.out.splitlines()[0].startswith("Commit: ")


# M5 (AC4)


def test_a_local_origin_writes_no_file_and_runs_no_gh(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr(clone, 7, "One")
    made = fake(monkeypatch, github=False)
    assert run(clone, monkeypatch, "--notes-url", NOTES_URL) == 0
    captured = capsys.readouterr()
    assert made.gh_calls == []
    assert not state.exists()
    assert captured.out.splitlines()[0].startswith("Commit: ")
    assert captured.err == ""


def test_dry_run_writes_no_file_and_runs_no_gh(
    repo: tuple[Path, Path],  # noqa: F811
    state: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    origin, clone = repo
    merge_pr(clone, 7, "One")
    before = remote_refs(origin)
    made = fake(monkeypatch)
    assert run(clone, monkeypatch, "--dry-run", "--notes-url", NOTES_URL) == 0
    captured = capsys.readouterr()
    assert made.gh_calls == []
    assert not state.exists()
    assert captured.out.splitlines()[0].startswith("Commit: ")
    assert "Release page" not in captured.out
    assert remote_refs(origin) == before


# M6 (AC5)


def test_configure_keeps_the_state_folder_of_the_flow_config() -> None:
    from ops import flow_config

    assert release.STATE_DIR == flow_config.load().loop_state_dir


def test_readme_release_section_names_the_option_and_the_release_page() -> None:
    text = README.read_text()
    section = text.split("\n## Release\n", 1)[1].split("\n## ", 1)[0]
    assert "--notes-url" in section
    assert "Release page" in section
