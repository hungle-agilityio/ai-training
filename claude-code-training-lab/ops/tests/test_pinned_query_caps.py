"""#406: ops/pinned_tests.py sees every query-cap test an issue touches. Run: pytest ops/tests"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ops import pinned_tests

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "pinned"


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


MAX_CAP = (
    "def test_cap(client: object, django_assert_max_num_queries: object) -> None:\n"
    "    with django_assert_max_num_queries(3):\n"
    "        client.get('/settings/')\n"
)
EXACT_CAP = (
    "def test_exact(client: object, django_assert_num_queries: object) -> None:\n"
    "    with django_assert_num_queries(2):\n"
    "        client.get(f'/locations/{1}/')\n"
)
CAPTURE_CAP = (
    "from django.test.utils import CaptureQueriesContext\n\n\n"
    "def test_capture(client: object) -> None:\n"
    "    with CaptureQueriesContext(connection) as ctx:\n"
    "        client.get('/dashboard/')\n"
    "    assert len(ctx) <= 4\n"
)
NO_LITERAL = (
    "LIMIT = 5\n\n\n"
    "def test_named(client: object, django_assert_max_num_queries: object) -> None:\n"
    "    with django_assert_max_num_queries(LIMIT):\n"
    "        client.get('/reviews/')\n"
)


# AC1: every kind of query-cap test


@pytest.mark.parametrize(
    ("source", "line"),
    [
        (MAX_CAP, "- `reviews/tests/test_a.py::test_cap`: query cap 3"),
        (EXACT_CAP, "- `reviews/tests/test_a.py::test_exact`: query cap 2"),
        (CAPTURE_CAP, "- `reviews/tests/test_a.py::test_capture`: query cap 4"),
        (NO_LITERAL, "- `reviews/tests/test_a.py::test_named`: query cap"),
    ],
    ids=["max", "exact", "capture", "no-literal"],
)
def test_each_kind_of_query_cap_is_listed_with_its_number(
    project: Path, source: str, line: str
) -> None:
    write(project, "reviews/tests/test_a.py", source)
    assert pinned_tests.find_pins(touched("reviews/views.py"), project) == [line]


def test_a_query_cap_is_not_listed_without_query_code(project: Path) -> None:
    write(project, "reviews/tests/test_a.py", MAX_CAP)
    assert pinned_tests.find_pins(touched("reviews/forms.py"), project) == []


# AC2: the URLs the issue names


def caps(project: Path) -> None:
    write(project, "reviews/tests/test_settings.py", MAX_CAP)
    write(project, "reviews/tests/test_location.py", EXACT_CAP)
    write(project, "reviews/tests/test_dashboard.py", CAPTURE_CAP)


def test_named_urls_keep_only_the_caps_that_request_them(project: Path) -> None:
    caps(project)
    body = "Shows a panel on `/settings/`.\n\n" + touched("reviews/views.py")
    assert pinned_tests.find_pins(body, project) == [
        "- `reviews/tests/test_settings.py::test_cap`: query cap 3"
    ]


def test_a_url_is_matched_on_the_part_before_the_first_angle_bracket(project: Path) -> None:
    caps(project)
    body = "The page `/locations/<id>/` gets a panel.\n\n" + touched("reviews/views.py")
    assert pinned_tests.find_pins(body, project) == [
        "- `reviews/tests/test_location.py::test_exact`: query cap 2"
    ]


def test_without_a_named_url_every_cap_is_listed(project: Path) -> None:
    caps(project)
    lines = pinned_tests.find_pins(touched("reviews/views.py"), project)
    assert len(lines) == 3


# AC3: common file names and plugin tests


@pytest.mark.parametrize(
    "name",
    ["views.py", "services.py", "repositories.py", "models.py", "urls.py", "forms.py", "app.css"],
)
def test_a_common_file_name_is_not_a_name_match(project: Path, name: str) -> None:
    write(project, "reviews/tests/test_a.py", f"def test_one() -> None:\n    assert '{name}'\n")
    assert pinned_tests.find_pins(touched(f"reviews/{name}"), project) == []


def plugin_test(project: Path) -> None:
    write(
        project.parent / "plugins" / "agent-flow",
        "skills/x/tests/test_a.py",
        "def test_one() -> None:\n    assert 'location.html'\n",
    )


def test_plugin_tests_are_skipped_for_an_app_only_issue(project: Path) -> None:
    plugin_test(project)
    body = touched("reviews/templates/reviews/location.html", "reviewradar/urls.py")
    assert pinned_tests.find_pins(body, project) == []


def test_plugin_tests_stay_when_a_flow_path_is_listed(project: Path) -> None:
    plugin_test(project)
    body = touched("reviews/templates/reviews/location.html", "ops/agent_tick.py")
    assert pinned_tests.find_pins(body, project) == [
        "- `../plugins/agent-flow/skills/x/tests/test_a.py::test_one`: names location.html"
    ]


# AC4: --unlisted


def run_main(args: list[str], monkeypatch: pytest.MonkeyPatch, project: Path) -> int:
    monkeypatch.setattr(pinned_tests, "PROJECT", project)
    monkeypatch.setattr(sys, "argv", ["pinned_tests.py", *args])
    return pinned_tests.main()


def test_unlisted_prints_the_hits_the_body_does_not_name_and_exits_one(
    project: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    caps(project)
    body = tmp_path / "body.md"
    body.write_text(
        "## Existing tests that change\n\n- `reviews/tests/test_settings.py::test_cap`: 3 to 4\n\n"
        "The dashboard test `test_dashboard.py` stays unchanged.\n\n" + touched("reviews/views.py")
    )
    assert run_main(["--unlisted", str(body)], monkeypatch, project) == 1
    assert capsys.readouterr().out.splitlines() == [
        "- `reviews/tests/test_location.py::test_exact`: query cap 2"
    ]


def test_unlisted_exits_zero_when_every_hit_is_named(
    project: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write(project, "reviews/tests/test_settings.py", MAX_CAP)
    body = tmp_path / "body.md"
    body.write_text("`test_cap` stays unchanged.\n\n" + touched("reviews/views.py"))
    assert run_main(["--unlisted", str(body)], monkeypatch, project) == 0
    assert capsys.readouterr().out == ""


def test_the_plain_run_still_exits_zero_with_hits(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    caps(project)
    body = tmp_path / "body.md"
    body.write_text(touched("reviews/views.py"))
    assert run_main([str(body)], monkeypatch, project) == 0


# AC5: the two real cases, as first posted


def real(name: str) -> list[str]:
    return pinned_tests.find_pins((FIXTURES / name).read_text(), pinned_tests.PROJECT)


def test_issue_397_lists_both_settings_caps_in_at_most_fifteen_lines() -> None:
    lines = real("issue-397.md")
    assert len(lines) <= 15
    for test in (
        "reviews/tests/integration/test_settings_page.py::test_get_makes_at_most_two_queries",
        "reviews/tests/integration/test_settings_suggestions.py::"
        "test_settings_page_makes_at_most_two_queries",
    ):
        assert f"- `{test}`: query cap 2" in lines


def test_issue_399_lists_the_three_location_caps_in_at_most_fifteen_lines() -> None:
    lines = real("issue-399.md")
    assert len(lines) <= 15
    for test in (
        "reviews/tests/integration/test_location_page.py::test_page_needs_at_most_four_queries",
        "reviews/tests/integration/test_location_trend.py::test_page_needs_at_most_four_queries",
        "reviews/tests/integration/test_location_topics.py::test_page_needs_at_most_five_queries",
    ):
        assert f"- `{test}`: query cap 5" in lines
