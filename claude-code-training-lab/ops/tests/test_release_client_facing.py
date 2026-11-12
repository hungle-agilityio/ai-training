"""ops/release.py lists merged pull requests as client-facing or internal (AC1, AC2).

Run: uv run pytest -q --no-cov ops/tests/test_release_client_facing.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ops import flow_config
from ops.tests.test_release import CLOSING_NOW, git, repo, run  # noqa: F401

CLIENT_HEADER = "Client-facing pull requests:"
INTERNAL_HEADER = "Internal pull requests:"
NONE_LINE = "  (none)"


def merge_pr_file(clone: Path, number: int, title: str, relative: str) -> str:
    """Merge a pull request that changes one file inside the app folder."""
    app_dir = flow_config.load().project_app_dir
    git(clone, "switch", "-c", f"feat/{number}")
    target = clone / app_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(title)
    git(clone, "add", ".")
    git(clone, "commit", "-m", f"work {number}")
    git(clone, "switch", "main")
    git(
        clone,
        "merge",
        "--no-ff",
        f"feat/{number}",
        "-m",
        f"Merge pull request #{number} from owner/feat/{number}",
        "-m",
        title,
    )
    git(clone, "push", "origin", "main")
    return git(clone, "rev-parse", "HEAD")


def groups(out: str) -> tuple[list[str], list[str]]:
    """Return the lines under the client-facing header and under the internal header."""
    lines = out.splitlines()
    client_at = lines.index(CLIENT_HEADER)
    internal_at = lines.index(INTERNAL_HEADER)
    assert client_at < internal_at
    client = lines[client_at + 1 : internal_at]
    internal: list[str] = []
    for line in lines[internal_at + 1 :]:
        if not line.startswith("  "):
            break
        internal.append(line)
    return client, internal


def test_m20_merge_changing_reviews_is_client_facing_and_specs_only_is_internal(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr_file(clone, 7, "Add the filter", "reviews/views.py")
    merge_pr_file(clone, 8, "Write the spec", "specs/x/spec.md")
    assert run(clone, monkeypatch, "--dry-run") == 0
    client, internal = groups(capsys.readouterr().out)
    assert client == ["  #7 Add the filter"]
    assert internal == ["  #8 Write the spec"]


def test_m21_dry_run_prints_both_groups_in_place_of_merged_pull_requests(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    head = merge_pr_file(clone, 8, "Write the spec", "specs/x/spec.md")
    merge_pr_file(clone, 7, "Add the filter", "reviews/views.py")
    head = git(clone, "rev-parse", "HEAD")
    assert run(clone, monkeypatch, "--dry-run") == 0
    out = capsys.readouterr().out
    assert "Merged pull requests:" not in out
    assert CLIENT_HEADER in out and INTERNAL_HEADER in out
    assert out.index(CLIENT_HEADER) < out.index("#7 Add the filter")
    assert out.index("#7 Add the filter") < out.index(INTERNAL_HEADER)
    assert out.index(INTERNAL_HEADER) < out.index("#8 Write the spec")
    assert head[:7] in out and "release/sprint-1" in out and "v2026.10.31" in out


def test_m21_real_release_prints_groups_and_keeps_the_last_line(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    origin, clone = repo
    merge_pr_file(clone, 7, "Add the filter", "reviews/views.py")
    head = merge_pr_file(clone, 8, "Write the spec", "specs/x/spec.md")
    assert run(clone, monkeypatch) == 0
    out = capsys.readouterr().out
    assert "Merged pull requests:" not in out
    client, internal = groups(out)
    assert client == ["  #7 Add the filter"]
    assert internal[:1] == ["  #8 Write the spec"]
    assert git(origin, "rev-parse", "deploy") == head
    assert out.strip().splitlines()[-1] == "Render deploys branch deploy after Checks pass."


def test_m22_only_internal_merge_new_shows_none_in_client_facing_group(
    repo: tuple[Path, Path],  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _, clone = repo
    merge_pr_file(clone, 8, "Write the spec", "specs/x/spec.md")
    assert run(clone, monkeypatch, "--dry-run") == 0
    client, internal = groups(capsys.readouterr().out)
    assert client == [NONE_LINE]
    assert internal == ["  #8 Write the spec"]
