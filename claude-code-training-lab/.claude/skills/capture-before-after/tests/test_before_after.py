"""Tests of the before and after capture (without a browser).

Run: uv run pytest .claude/skills/capture-before-after/tests --no-cov -q
"""

import subprocess
from collections.abc import Callable
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

SKILL = Path(__file__).resolve().parents[1]
Runner = Callable[[list[str], Path], tuple[int, str]]


def load() -> ModuleType:
    spec = util.spec_from_file_location("before_after", SKILL / "before_after.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BA = load()


def shot(folder: Path, name: str, content: bytes) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.png").write_bytes(content)
    return f"{name}.png"


def result(folder: Path, name: str, status: int | None, content: bytes) -> dict[str, object]:
    return {
        "name": name,
        "url": f"/{name}/",
        "http_status": status,
        "screenshot": shot(folder, name, content),
    }


def test_pairs_are_labelled_changed_same_new_or_missing(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    steps_before = [
        result(before, "same", 200, b"one"),
        result(before, "changed", 200, b"old"),
        result(before, "new-page", 404, b"404"),
    ]
    steps_after = [
        result(after, "same", 200, b"one"),
        result(after, "changed", 200, b"new"),
        result(after, "new-page", 200, b"page"),
    ]

    pairs = {p["name"]: p for p in BA.pair_steps(steps_before, before, steps_after, after)}

    assert pairs["same"]["label"] == "no visible difference"
    assert pairs["changed"]["label"] == "changed"
    assert pairs["new-page"]["label"] == "did not exist before"


def test_a_step_missing_on_one_side_is_reported(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    steps_before = [result(before, "a", 200, b"x")]
    steps_after = [result(after, "a", 200, b"x"), result(after, "b", 200, b"y")]

    pairs = {p["name"]: p for p in BA.pair_steps(steps_before, before, steps_after, after)}

    assert pairs["b"]["label"] == "not captured before"
    assert (
        BA.pair_steps(steps_after, after, steps_before, before)[1]["label"] == "not captured after"
    )


def test_the_html_shows_both_images_the_labels_and_escapes_text(tmp_path: Path) -> None:
    before, after = tmp_path / "before", tmp_path / "after"
    pairs = BA.pair_steps(
        [result(before, "a<b>", 200, b"1")], before, [result(after, "a<b>", 200, b"2")], after
    )

    page = BA.render_compare_html("Title <x>", "main", "HEAD", pairs)

    assert page.count("data:image/png;base64,") == 2
    assert "changed" in page and "&lt;x&gt;" in page and "<x>" not in page


def test_the_base_is_the_given_ref_or_the_merge_base_with_main() -> None:
    calls: list[list[str]] = []

    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        calls.append(args)
        if args[:2] == ["git", "show"]:
            return 0, "manage"
        if args[:2] == ["git", "merge-base"]:
            return 0, "abc123\n"
        return 1, ""

    assert BA.resolve_base(Path("."), "feat/x", run) == "feat/x"
    assert BA.resolve_base(Path("."), None, run) == "abc123"
    assert ["git", "merge-base", "main", "HEAD"] in calls


def test_without_a_base_a_main_that_has_no_project_is_an_error() -> None:
    def run(args: list[str], cwd: Path) -> tuple[int, str]:
        return 128, "fatal"

    with pytest.raises(ValueError, match="--base"):
        BA.resolve_base(Path("."), None, run)


def git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout


def test_checkout_makes_a_temporary_worktree_of_the_ref_and_removes_it(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "manage.py").write_text("one")
    git(repo, "add", "manage.py")
    git(repo, "commit", "-q", "-m", "first")
    first = git(repo, "rev-parse", "HEAD").strip()
    (repo / "manage.py").write_text("two")
    git(repo, "commit", "-qam", "second")

    with BA.checkout(repo, first) as tree:
        assert (tree / "manage.py").read_text() == "one"
        location = tree
    assert not location.exists()
    assert str(location) not in git(repo, "worktree", "list")
    assert (repo / "manage.py").read_text() == "two"


def test_the_project_folder_in_a_worktree_follows_the_prefix() -> None:
    assert BA.project_in(Path("/tmp/tree"), "claude-code-training-lab/") == Path(
        "/tmp/tree/claude-code-training-lab"
    )
    assert BA.project_in(Path("/tmp/tree"), "") == Path("/tmp/tree")


def test_the_prefix_printed_by_git_may_end_with_a_new_line() -> None:
    assert BA.project_in(Path("/tmp/tree"), "claude-code-training-lab/\n") == Path(
        "/tmp/tree/claude-code-training-lab"
    )
    assert BA.project_in(Path("/tmp/tree"), "\n") == Path("/tmp/tree")


def test_masking_of_both_sides_must_be_clean() -> None:
    clean = {"masking": {"status": "clean", "findings": []}}
    leaked = {"masking": {"status": "findings", "findings": [{"step": "a", "kinds": ["email"]}]}}

    assert BA.combined_masking(clean, clean)["status"] == "clean"
    assert BA.combined_masking(clean, leaked)["status"] == "findings"
    assert BA.combined_masking(clean, leaked)["findings"][0]["step"] == "a"
