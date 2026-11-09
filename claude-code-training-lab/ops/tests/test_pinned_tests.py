"""ops/pinned_tests.py: which existing tests an issue would change. Run: pytest ops/tests"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ops import pinned_tests

NOTHING = "No existing test pins this task."


def write(project: Path, rel: str, text: str) -> None:
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "plugins-parent" / "app"
    root.mkdir(parents=True)
    return root


def touched(*paths: str) -> str:
    return "## Files likely touched\n\n" + "\n".join(f"- `{p}`" for p in paths) + "\n"


def test_a_backticked_identifier_in_the_test_source_is_listed(project: Path) -> None:
    write(project, "ops/tests/test_a.py", "def test_one() -> None:\n    assert build_prompt()\n")

    lines = pinned_tests.find_pins("Change `build_prompt` text.", project)

    assert lines == ["- `ops/tests/test_a.py::test_one`: names build_prompt"]


def test_a_name_in_a_helper_the_test_calls_is_listed(project: Path) -> None:
    source = (
        "def helper() -> str:\n    return 'build_prompt'\n\n\n"
        "def test_uses() -> None:\n    assert helper()\n\n\n"
        "def test_other() -> None:\n    assert True\n"
    )
    write(project, "ops/tests/test_a.py", source)

    lines = pinned_tests.find_pins("`build_prompt`", project)

    assert lines == ["- `ops/tests/test_a.py::test_uses`: names build_prompt"]


def test_a_name_in_a_module_constant_the_test_reads_is_listed(project: Path) -> None:
    source = "PATTERN = 'bulk_create'\n\n\ndef test_uses() -> None:\n    assert PATTERN\n"
    write(project, "reviews/tests/unit/test_a.py", source)

    lines = pinned_tests.find_pins("`bulk_create`", project)

    assert lines == ["- `reviews/tests/unit/test_a.py::test_uses`: names bulk_create"]


def test_a_file_name_is_matched(project: Path) -> None:
    write(
        project, "reviews/tests/test_a.py", "def test_one() -> None:\n    assert 'location.html'\n"
    )

    assert pinned_tests.find_pins("`location.html`", project) == [
        "- `reviews/tests/test_a.py::test_one`: names location.html"
    ]


def test_a_path_is_matched_by_its_file_name(project: Path) -> None:
    write(
        project, "reviews/tests/test_a.py", "def test_one() -> None:\n    assert 'location.html'\n"
    )

    lines = pinned_tests.find_pins(touched("reviews/templates/reviews/location.html"), project)

    assert lines == ["- `reviews/tests/test_a.py::test_one`: names location.html"]


def test_a_longer_word_does_not_match_a_name(project: Path) -> None:
    write(
        project, "ops/tests/test_a.py", "def test_one() -> None:\n    assert build_prompt_two()\n"
    )

    assert pinned_tests.find_pins("`build_prompt`", project) == []


def test_a_test_method_in_a_class_is_listed(project: Path) -> None:
    source = "class TestA:\n    def test_one(self) -> None:\n        assert build_prompt()\n"
    write(project, "ops/tests/test_a.py", source)

    assert pinned_tests.find_pins("`build_prompt`", project) == [
        "- `ops/tests/test_a.py::test_one`: names build_prompt"
    ]


def test_plugin_tests_are_listed_with_their_relative_path(project: Path) -> None:
    rel = "skills/x/tests/test_a.py"
    write(
        project.parent / "plugins" / "agent-flow",
        rel,
        "def test_one() -> None:\n    build_prompt\n",
    )

    assert pinned_tests.find_pins("`build_prompt`", project) == [
        f"- `../plugins/agent-flow/{rel}::test_one`: names build_prompt"
    ]


@pytest.mark.parametrize("ignored", ["abc", "main", "None", "True", "False"])
def test_short_and_common_names_are_ignored(project: Path, ignored: str) -> None:
    write(project, "ops/tests/test_a.py", f"def test_one() -> None:\n    {ignored}\n")

    assert pinned_tests.find_pins(f"`{ignored}`", project) == []


@pytest.mark.parametrize("mark", ["(NEW)", "(NEW test file)"])
def test_a_path_marked_new_is_never_a_name(project: Path, mark: str) -> None:
    write(project, "ops/tests/test_a.py", "def test_one() -> None:\n    assert 'fresh_tool.py'\n")
    section = f"## Files likely touched\n\n- `ops/fresh_tool.py` {mark}\n"
    body = f"AC names `ops/fresh_tool.py`.\n\n{section}"

    assert pinned_tests.find_pins(body, project) == []


COUNTING = (
    "def test_count(django_assert_num_queries: object) -> None:\n"
    "    assert django_assert_num_queries\n"
)
UNITTEST_COUNTING = "def test_count(self: object) -> None:\n    self.assertNumQueries(2)\n"


@pytest.mark.parametrize(
    "path",
    [
        "reviews/views.py",
        "reviews/import_views.py",
        "reviews/services.py",
        "reviews/reply_service.py",
        "reviews/repositories.py",
        "reviews/reply_repository.py",
        "reviews/templates/reviews/replies.html",
        "claude-code-training-lab/reviews/views.py",
    ],
)
def test_a_query_count_test_is_listed_when_query_code_is_touched(project: Path, path: str) -> None:
    write(project, "reviews/tests/test_a.py", COUNTING)

    assert pinned_tests.find_pins(touched(path), project) == [
        "- `reviews/tests/test_a.py::test_count`: query count"
    ]


def test_assert_num_queries_counts_as_a_query_count_test(project: Path) -> None:
    write(project, "reviews/tests/test_a.py", UNITTEST_COUNTING)

    assert pinned_tests.find_pins(touched("reviews/views.py"), project) == [
        "- `reviews/tests/test_a.py::test_count`: query count"
    ]


@pytest.mark.parametrize(
    "body",
    [
        touched("reviews/forms.py"),
        touched("reviews/static/reviews/app.css"),
        touched("ops/services.py"),
        touched("reviews/tests/integration/test_views.py"),
        "## Files likely touched\n\n- `reviews/new_service.py` (NEW)\n",
        "Mentions `reviews/services.py` outside the section.\n\n## Files likely touched\n",
    ],
)
def test_a_query_count_test_is_not_listed_for_other_files(project: Path, body: str) -> None:
    write(project, "reviews/tests/test_a.py", COUNTING)

    lines = pinned_tests.find_pins(body, project)

    assert not [line for line in lines if line.endswith("query count")]


def test_a_test_file_that_does_not_parse_is_skipped(project: Path) -> None:
    write(project, "ops/tests/test_broken.py", "def test_one(:\n")
    write(project, "ops/tests/test_good.py", "def test_two() -> None:\n    build_prompt\n")

    assert pinned_tests.find_pins("`build_prompt`", project) == [
        "- `ops/tests/test_good.py::test_two`: names build_prompt"
    ]


def run_main(args: list[str], monkeypatch: pytest.MonkeyPatch, project: Path) -> int:
    monkeypatch.setattr(pinned_tests, "PROJECT", project)
    monkeypatch.setattr(sys, "argv", ["pinned_tests.py", *args])
    return pinned_tests.main()


def test_main_says_so_when_nothing_matches(
    project: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    body = tmp_path / "body.md"
    body.write_text("No names here.")

    code = run_main([str(body)], monkeypatch, project)

    assert code == 0
    assert capsys.readouterr().out.strip() == NOTHING


def test_main_prints_one_line_per_test_and_writes_nothing(
    project: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write(project, "ops/tests/test_a.py", "def test_one() -> None:\n    build_prompt\n")
    body = tmp_path / "body.md"
    body.write_text("`build_prompt`")
    before = sorted(tmp_path.rglob("*"))

    code = run_main([str(body)], monkeypatch, project)

    assert code == 0
    assert capsys.readouterr().out.splitlines() == [
        "- `ops/tests/test_a.py::test_one`: names build_prompt"
    ]
    assert sorted(tmp_path.rglob("*")) == before


@pytest.mark.parametrize("args", [[], ["/no/such/body.md"]])
def test_main_exits_zero_without_a_readable_body(
    project: Path, monkeypatch: pytest.MonkeyPatch, args: list[str]
) -> None:
    assert run_main(args, monkeypatch, project) == 0


def test_real_case_epic_prompt() -> None:
    lines = pinned_tests.find_pins("`epic_prompt`", pinned_tests.PROJECT)

    wanted = (
        "ops/tests/test_epic_stacked_start.py::"
        "test_a_task_with_two_dependencies_in_the_epic_branch_starts_on_it"
    )
    assert f"- `{wanted}`: names epic_prompt" in lines


def test_real_case_bulk_create() -> None:
    lines = pinned_tests.find_pins("`bulk_create`", pinned_tests.PROJECT)

    wanted = (
        "reviews/tests/unit/test_review_create_paths.py::"
        "test_reviews_are_created_only_through_the_repository"
    )
    assert f"- `{wanted}`: names bulk_create" in lines
