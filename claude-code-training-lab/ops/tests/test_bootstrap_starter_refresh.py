"""`bootstrap.py --stack` writes a complete, current starter: every cited decision record.

Spec: specs/starter-refresh/spec.md (AC1 to AC8).
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

from ops import bootstrap

REPO = "acme/garden"
SOURCE = Path(__file__).resolve().parents[2]
ADR_NUMBERS = range(8, 34)
INDEX_LINE = re.compile(r"^- \[(ADR-\d{3}): .+\]\((ADR-\d{3}-[^)]+\.md)\)$")
README_LINE = (
    "The clickable prototype of the whole app, prototype.html (ADR-030);"
    " one file, every screen and state.\n"
)
Run = Callable[..., int]


@pytest.fixture
def target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    path = tmp_path / "garden"
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{REPO}.git"], cwd=path, check=True
    )
    return path


@pytest.fixture
def run(target: Path) -> Run:
    def call(*extra: str) -> int:
        argv = [
            "--target", str(target), "--repo", REPO, "--owner", "acme-owner",
            "--name", "Garden", "--slug", "garden", "--ntfy-topic", "garden-test", "--no-labels",
        ]  # fmt: skip
        return bootstrap.main([*argv, *extra])

    return call


def text_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.relative_to(root).parts:
            continue
        try:
            path.read_text()
        except UnicodeDecodeError:
            continue
        found.append(path)
    return found


def decisions(target: Path) -> list[Path]:
    return sorted((target / "docs" / "decisions").glob("ADR-*.md"))


# M1 (AC1)


def test_stack_output_writes_adr_008_to_adr_033(run: Run, target: Path) -> None:
    assert run("--stack", "python") == 0
    names = [p.name for p in decisions(target)]
    assert len(names) == 26
    assert [int(n[4:7]) for n in names] == list(ADR_NUMBERS)


def test_manifest_copies_the_fourteen_records_right_after_adr_019() -> None:
    manifest = tomllib.loads((SOURCE / "ops" / "bootstrap_manifest.toml").read_text())
    paths = [entry["path"] for entry in manifest["copy"]]
    prefix = ".claude/knowledge/decisions/ADR-"
    adrs = [p for p in paths if p.startswith(prefix)]
    after = paths.index(next(p for p in adrs if "ADR-019-" in p)) + 1
    following = paths[after : after + 14]
    assert [Path(p).name[4:7] for p in following] == [f"{n:03d}" for n in range(20, 34)]
    assert all(e["scope"] == "app" for e in manifest["copy"] if e["path"] in following)


# M2 (AC2)


def test_every_adr_cited_under_claude_and_plugin_has_its_file(run: Run, target: Path) -> None:
    run("--stack", "python")
    have = {p.name[:7] for p in decisions(target)}
    missing: list[str] = []
    for folder in (target / ".claude", target / ".flow" / "plugin"):
        for path in folder.rglob("*.md"):
            for cited in set(re.findall(r"ADR-\d{3}", path.read_text(errors="replace"))):
                if cited not in have:
                    missing.append(f"{path.relative_to(target)}: {cited}")
    assert missing == []


# M3 (AC3)


def test_index_links_exactly_the_copied_records(run: Run, target: Path) -> None:
    run("--stack", "python")
    text = (target / "docs" / "decisions" / "README.md").read_text()
    after = text.split("\n## Index\n", 1)[1]
    items = [line for line in after.splitlines() if line.startswith("- ")]
    matches = [INDEX_LINE.match(line) for line in items]
    assert all(matches), items
    linked = [m.group(2) for m in matches if m]
    assert linked == [p.name for p in decisions(target)]
    assert all(m.group(1) == m.group(2)[:7] for m in matches if m)


def test_index_head_keeps_the_source_lines(run: Run, target: Path) -> None:
    run("--stack", "python")
    out = (target / "docs" / "decisions" / "README.md").read_text()
    source = (SOURCE / ".claude" / "knowledge" / "decisions" / "README.md").read_text()
    assert out.split("## Index", 1)[0] == source.split("## Index", 1)[0]


def test_old_layout_readme_is_the_source_readme(run: Run, target: Path) -> None:
    assert run("--app-dir", "app") == 0
    copied = target / "app" / ".claude" / "knowledge" / "decisions" / "README.md"
    source = SOURCE / ".claude" / "knowledge" / "decisions" / "README.md"
    assert copied.read_bytes() == source.read_bytes()


def test_old_layout_copies_the_fourteen_records_as_plain_files(run: Run, target: Path) -> None:
    assert run("--app-dir", "app") == 0
    folder = target / "app" / ".claude" / "knowledge" / "decisions"
    for number in range(20, 34):
        assert len(list(folder.glob(f"ADR-{number:03d}-*.md"))) == 1


# M4 (AC4)


def test_no_copied_text_mentions_design_app(run: Run, target: Path) -> None:
    run("--stack", "python")
    hits = [p.relative_to(target) for p in text_files(target) if "design/app/" in p.read_text()]
    assert hits == []


def test_copied_build_report_defaults_to_the_new_prototype_place(run: Run, target: Path) -> None:
    run("--stack", "python")
    path = target / ".flow" / "plugin" / "skills" / "build-verify-report" / "build_report.py"
    text = path.read_text()
    assert 'PROTOTYPE = Path("docs") / "design" / "prototype.html"' in text
    assert 'Path("design") / "app"' not in text
    help_line = next(line for line in text.splitlines() if '"--design", type=Path' in line)
    block = "\n".join(text.splitlines()[text.splitlines().index(help_line) :][:6])
    assert "docs/design/prototype.html" in block


def test_plugin_source_keeps_its_prototype_default() -> None:
    path = SOURCE.parent / "plugins" / "agent-flow" / "skills" / "build-verify-report"
    assert (
        'PROTOTYPE = Path("design") / "app" / "prototype.html"'
        in (path / "build_report.py").read_text()
    )


# M5 (AC5)


def test_flow_toml_paths_hold_the_design_folder(run: Run, target: Path) -> None:
    run("--stack", "python")
    paths = tomllib.loads((target / ".flow" / "flow.toml").read_text())["paths"]
    assert paths["spec_pr_dirs"] == ["docs/intent", "docs/specs", "docs/design"]
    flow_dirs = paths["flow_dirs"]
    assert "docs/design/" in flow_dirs
    assert flow_dirs.index("docs/design/") == flow_dirs.index("docs/specs/") + 1


# M6 (AC6, AC7)


def test_project_instructions_name_the_three_spec_folders(run: Run, target: Path) -> None:
    run("--stack", "python")
    text = (target / ".claude" / "project-instructions.md").read_text()
    assert "`docs/intent/`, `docs/specs/` and `docs/design/`" in text
    assert "`specs/` and `design/`" not in text
    mentions = re.findall(r"(\S*)prototype\.html", text)
    assert mentions and all(m.endswith("docs/design/") for m in mentions)


def test_design_folder_has_the_one_line_readme(run: Run, target: Path) -> None:
    run("--stack", "python")
    assert (target / "docs" / "design" / "README.md").read_text() == README_LINE


# M7 (AC8)


def test_no_text_file_of_the_output_mentions_reviewradar_variables(run: Run, target: Path) -> None:
    run("--stack", "python")
    hits = [p.relative_to(target) for p in text_files(target) if "REVIEWRADAR_" in p.read_text()]
    assert hits == []


def test_adr_032_copy_names_the_variables_after_the_project(run: Run, target: Path) -> None:
    run("--stack", "python")
    text = next((target / "docs" / "decisions").glob("ADR-032-*.md")).read_text()
    assert "a password variable named after Garden" in text
    assert "a variable named after Garden" in text
    assert "REVIEWRADAR_" not in text


def test_source_adr_032_is_unchanged() -> None:
    text = next((SOURCE / ".claude" / "knowledge" / "decisions").glob("ADR-032-*.md")).read_text()
    assert "`REVIEWRADAR_DEMO_PASSWORD`" in text and "a `REVIEWRADAR_` name" in text
