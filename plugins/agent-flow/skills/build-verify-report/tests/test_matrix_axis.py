"""Tests of the Test matrix axis of the verify report: one line per row of the issue's matrix.

Run: uv run pytest <this folder>/test_matrix_axis.py --no-cov -q
"""

import json
from collections.abc import Callable
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[1]
PLUGIN = SKILL.parents[1]
Runner = Callable[[list[str], Path], tuple[int, str]]
NO_MATRIX = "the issue has no test matrix rows"
EMPTY = "the matrix list is empty"


def load() -> ModuleType:
    spec = util.spec_from_file_location("build_report", SKILL / "build_report.py")
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = load()


def run(args: list[str], cwd: Path) -> tuple[int, str]:
    """Every command of the report is green."""
    text = " ".join(args)
    if "ruff" in text:
        return 0, "All checks passed!\n"
    if "mypy" in text:
        return 0, "Success: no issues found in 28 source files\n"
    if "coverage report" in text:
        return 0, "Name Stmts\nTOTAL 204 0 100%\n"
    if "hooks/tests" in text:
        return 0, "176 passed in 2.2s\n"
    if "pytest" in text:
        return 0, "TOTAL   1020   3   99%\n142 passed in 1.2s\n"
    if args[:2] == ["git", "diff"]:
        return 0, ""
    return 0, "feat/x\n"


def entry(row: str, status: str = "PASS", test: str = "tests/test_a.py::test_a") -> dict[str, str]:
    return {"row": row, "ac": "AC1", "test": test, "status": status, "evidence": "1 passed"}


def criteria(matrix: Any = None, with_matrix: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "criteria": [{"text": "AC1. a rule", "status": "PASS", "evidence": "a test"}],
        "check_yourself": [],
    }
    if with_matrix:
        data["matrix"] = matrix
    return data


def build(tmp_path: Path, data: dict[str, Any] | None) -> dict[str, Any]:
    root = tmp_path / "project"
    tests = root / "app" / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_q.py").write_text("def test_q(django_assert_num_queries):\n    pass\n")
    report: dict[str, Any] = BUILD.build(
        root, tmp_path / "out", run, "Issue", data, None, False, False, no_ui=True
    )
    return report


def page_report(matrix: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "title": "Issue",
        "verdict": "PASS",
        "branch": "b",
        "commit": "c",
        "date": "d",
        "axes": [{"name": "Lint", "status": "PASS", "evidence": "ok"}],
        "matrix": matrix,
    }


# M1: every row passes or is manual


def test_rows_all_pass_or_manual_give_pass_with_the_counts() -> None:
    rows = [entry("M1"), entry("M2"), entry("M3", "MANUAL", "Open the page and look")]

    axis = BUILD.matrix_axis(criteria(rows))

    assert axis == {
        "name": "Test matrix",
        "status": "PASS",
        "evidence": "2 of 3 rows pass, 1 manual",
    }


def test_a_manual_row_needs_no_test_name() -> None:
    axis = BUILD.matrix_axis(criteria([entry("M1"), entry("M2", "MANUAL", "")]))

    assert axis["status"] == "PASS" and axis["evidence"] == "1 of 2 rows pass, 1 manual"


def test_the_matrix_axis_comes_right_after_the_issue_axis(tmp_path: Path) -> None:
    report = build(tmp_path, criteria([entry("M1")]))
    names = [a["name"] for a in report["axes"]]

    assert names[names.index("Issue") + 1] == "Test matrix"
    assert names.count("Test matrix") == 1
    assert report["verdict"] == "PASS"


# M2: a row that does not pass fails the axis and the verdict


@pytest.mark.parametrize(
    ("rows", "evidence"),
    [
        ([entry("M1"), entry("M2", "FAIL")], "1 of 2 rows fail: M2"),
        ([entry("M1", "SKIPPED"), entry("M2")], "1 of 2 rows fail: M1"),
        ([entry("M1", "pass")], "1 of 1 rows fail: M1"),
        ([entry("M1", "NOT CONFIGURED")], "1 of 1 rows fail: M1"),
        ([entry("M1", "PASS", "")], "1 of 1 rows fail: M1"),
        ([entry("M1", "PASS", "   ")], "1 of 1 rows fail: M1"),
        (
            [entry("M1"), entry("M2", "FAIL"), entry("M3", "MANUAL"), entry("M5", "PASS", " ")],
            "2 of 4 rows fail: M2, M5",
        ),
    ],
)
def test_a_row_that_does_not_pass_fails_the_axis(rows: list[dict[str, str]], evidence: str) -> None:
    axis = BUILD.matrix_axis(criteria(rows))

    assert axis["status"] == "FAIL" and axis["evidence"] == evidence


def test_a_pass_row_without_the_test_key_fails() -> None:
    row = {"row": "M4", "ac": "AC2", "status": "PASS", "evidence": "x"}

    assert BUILD.matrix_axis(criteria([row]))["evidence"] == "1 of 1 rows fail: M4"


@pytest.mark.parametrize("test", [None, 5, ["t.py::test_a"], {"a": 1}])
def test_a_pass_row_whose_test_is_not_text_fails(test: Any) -> None:
    row = {"row": "M4", "ac": "AC2", "test": test, "status": "PASS", "evidence": "x"}

    assert BUILD.matrix_axis(criteria([row]))["evidence"] == "1 of 1 rows fail: M4"


def test_a_row_without_a_status_fails() -> None:
    row = {"row": "M4", "ac": "AC2", "test": "t.py::test_a", "evidence": "x"}

    assert BUILD.matrix_axis(criteria([row]))["evidence"] == "1 of 1 rows fail: M4"


def test_an_entry_with_no_row_is_named_with_a_question_mark() -> None:
    nameless = {"ac": "AC1", "test": "t.py::test_a", "status": "FAIL", "evidence": "x"}

    axis = BUILD.matrix_axis(criteria([nameless, entry("M2", "FAIL")]))

    assert axis["evidence"] == "2 of 2 rows fail: ?, M2"


@pytest.mark.parametrize("matrix", [[], "M1", {"row": "M1"}, None, 3])
def test_an_empty_matrix_or_one_that_is_not_a_list_fails(matrix: Any) -> None:
    axis = BUILD.matrix_axis(criteria(matrix))

    assert axis == {"name": "Test matrix", "status": "FAIL", "evidence": EMPTY}


def test_an_entry_that_is_not_an_object_fails_as_a_nameless_row() -> None:
    axis = BUILD.matrix_axis(criteria([entry("M1"), "M2"]))

    assert axis["status"] == "FAIL" and axis["evidence"] == "1 of 2 rows fail: ?"


@pytest.mark.parametrize(
    "matrix",
    [[entry("M1"), entry("M2", "FAIL")], [entry("M1", "DONE")], [entry("M1", test="")], []],
)
def test_a_failing_matrix_makes_the_verdict_fail(tmp_path: Path, matrix: Any) -> None:
    report = build(tmp_path, criteria(matrix))
    axes = {a["name"]: a for a in report["axes"]}

    assert axes["Test matrix"]["status"] == "FAIL"
    assert [a["name"] for a in report["axes"] if a["status"] == "FAIL"] == ["Test matrix"]
    assert report["verdict"] == "FAIL"


# M3: no matrix


def test_criteria_without_a_matrix_are_not_applicable() -> None:
    expected = {"name": "Test matrix", "status": "NOT APPLICABLE", "evidence": NO_MATRIX}

    assert BUILD.matrix_axis(criteria(with_matrix=False)) == expected
    assert BUILD.matrix_axis(None) == expected
    assert BUILD.matrix_axis({}) == expected


@pytest.mark.parametrize("with_criteria", [True, False])
def test_no_matrix_leaves_the_verdict_as_it_was(tmp_path: Path, with_criteria: bool) -> None:
    report = build(tmp_path, criteria(with_matrix=False) if with_criteria else None)
    others = [a for a in report["axes"] if a["name"] != "Test matrix"]
    axes = {a["name"]: a for a in report["axes"]}

    assert axes["Test matrix"]["status"] == "NOT APPLICABLE"
    assert axes["Test matrix"]["evidence"] == NO_MATRIX
    assert report["verdict"] == BUILD.verdict(others)
    assert report["verdict"] == ("PASS" if with_criteria else "INCOMPLETE")


# M4: report.json and the two pages


def test_report_json_holds_the_matrix_as_given(tmp_path: Path) -> None:
    rows = [entry("M1"), entry("M2", "MANUAL", "Open the page")]

    report = build(tmp_path, criteria(rows))

    assert report["matrix"] == rows
    assert json.loads((tmp_path / "out" / "report.json").read_text())["matrix"] == rows


@pytest.mark.parametrize("with_criteria", [True, False])
def test_report_json_holds_an_empty_list_without_a_matrix(
    tmp_path: Path, with_criteria: bool
) -> None:
    report = build(tmp_path, criteria(with_matrix=False) if with_criteria else None)

    assert report["matrix"] == []
    assert json.loads((tmp_path / "out" / "report.json").read_text())["matrix"] == []
    for name in ("report.html", "report-share.html"):
        assert "<h2>Test matrix</h2>" not in (tmp_path / "out" / name).read_text()


def test_both_pages_show_one_line_per_row_after_the_axis_table() -> None:
    rows = [
        entry("M1"),
        {"row": "M2", "ac": "AC2", "test": "Open /x/", "status": "MANUAL", "evidence": "seen"},
        entry("M3", "FAIL"),
    ]
    line = (
        '<tr><td>M2</td><td>AC2</td><td>Open /x/</td><td class="MANUAL">MANUAL</td>'
        "<td>seen</td></tr>"
    )

    for page in (BUILD.render_html(page_report(rows)), BUILD.render_share_html(page_report(rows))):
        heading = page.index("<h2>Test matrix</h2>")
        table = page[heading:]
        assert page.index("<th>Axis</th>") < heading
        assert page.count("<h2>Test matrix</h2>") == 1
        for column in ("Row", "AC", "Test", "Status", "Evidence"):
            assert f"<th>{column}</th>" in table
        assert (
            table.index("<th>Row</th>")
            < table.index("<th>AC</th>")
            < table.index("<th>Test</th>")
            < table.index("<th>Status</th>")
            < table.index("<th>Evidence</th>")
        )
        assert line in table
        assert '<td class="PASS">PASS</td>' in table and '<td class="FAIL">FAIL</td>' in table
        assert table.count("<tr><td>") == 3


def test_the_matrix_table_is_before_the_screenshots_and_what_to_check(tmp_path: Path) -> None:
    (tmp_path / "01-a.png").write_bytes(b"png")
    report = {
        **page_report([entry("M1")]),
        "screenshots": [str(tmp_path / "01-a.png")],
        "review": "Status: PASS",
        "check_yourself": ["Open /x/"],
    }

    page = BUILD.render_share_html(report)

    assert (
        page.index("<th>Axis</th>")
        < page.index("<h2>Test matrix</h2>")
        < page.index("<h2>Screenshots</h2>")
        < page.index("<h2>Review</h2>")
        < page.index("<h2>What to check yourself</h2>")
    )


def test_every_value_of_a_row_is_escaped() -> None:
    row = {
        "row": "<i>M1</i>",
        "ac": "<b>AC1</b>",
        "test": "t.py::test_<x>",
        "status": '"><script>s()</script>',
        "evidence": "a & <u>b</u>",
    }

    for page in (
        BUILD.render_html(page_report([row])),
        BUILD.render_share_html(page_report([row])),
    ):
        table = page[page.index("<h2>Test matrix</h2>") :]
        for raw in ("<i>M1</i>", "<b>AC1</b>", "test_<x>", "<script>s()", "<u>b</u>"):
            assert raw not in table
        assert "&lt;i&gt;M1&lt;/i&gt;" in table and "&lt;b&gt;AC1&lt;/b&gt;" in table
        assert "t.py::test_&lt;x&gt;" in table and "a &amp; &lt;u&gt;b&lt;/u&gt;" in table
        assert 'class="&quot;&gt;&lt;script&gt;s()&lt;/script&gt;"' in table


def test_a_row_with_missing_keys_still_gets_a_line() -> None:
    page = BUILD.render_share_html(page_report([{"row": "M1"}]))

    assert "<h2>Test matrix</h2>" in page and "<td>M1</td>" in page


@pytest.mark.parametrize("report", [page_report([]), {**page_report([]), "matrix": None}])
def test_no_heading_and_no_table_without_entries(report: dict[str, Any]) -> None:
    del_key = {k: v for k, v in report.items() if k != "matrix"}

    for data in (report, del_key):
        for page in (BUILD.render_html(data), BUILD.render_share_html(data)):
            assert "Test matrix" not in page and "<th>Row</th>" not in page


def test_the_written_pages_show_the_table_of_the_build(tmp_path: Path) -> None:
    build(tmp_path, criteria([entry("M1"), entry("M2", "FAIL")]))

    for name in ("report.html", "report-share.html"):
        page = (tmp_path / "out" / name).read_text()
        assert "<h2>Test matrix</h2>" in page
        assert "<td>Test matrix</td>" in page and "1 of 2 rows fail: M2" in page


def test_the_matrix_text_is_scanned_for_personal_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []

    def status(browser_masking: dict[str, Any] | None, texts: list[str]) -> dict[str, Any]:
        seen.append(texts)
        return {"status": "clean", "findings": []}

    monkeypatch.setattr(BUILD, "masking_status", status)
    rows = [{**entry("M1"), "evidence": "a marker only the matrix holds"}]

    build(tmp_path, criteria(rows))

    assert len(seen) == 1 and json.dumps(rows) in seen[0]


# M5: the skill text and the plugin version


def test_the_skill_documents_the_matrix_list_and_the_axis() -> None:
    text = (SKILL / "SKILL.md").read_text()
    section = text[text.index("## The criteria file (you write it)") :]
    section = section[: section.index("\n## ", 5)]

    assert '"matrix"' in section and "Test matrix" in section
    for key in ('"row"', '"ac"', '"test"', '"status"', '"evidence"'):
        assert key in section
    for status in ("`PASS`", "`FAIL`", "`MANUAL`", "`NOT APPLICABLE`"):
        assert status in section
    assert NO_MATRIX in section and EMPTY in section
    assert "rows fail" in section and "rows pass" in section and "manual" in section


def test_the_plugin_version_is_1_0_20() -> None:
    data = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())

    assert data["version"] == "1.0.20"
