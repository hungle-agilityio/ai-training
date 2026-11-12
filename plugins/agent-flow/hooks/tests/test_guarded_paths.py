"""#526: the guarded-files rule lives once in guarded_paths.py; before-edit-check reads it.

Rows M1 (the module), M2 (the hook defines none of it, messages as on main), M3 (flow.toml).
"""

import ast
import subprocess
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

HOOKS = Path(__file__).resolve().parents[1]
HOOK = HOOKS / "before-edit-check.py"
MODULE = HOOKS / "guarded_paths.py"
LOOP = {"FLOW_LOOP": "1"}
NAMES = ("PROTECTED_DIRS", "PROTECTED_FILES", "PLUGIN_DIRS", "GATE_FILES", "guarded_kind")
GATE_NAMES = {
    "pyproject.toml",
    "uv.lock",
    "conftest.py",
    "ruff.toml",
    ".ruff.toml",
    "mypy.ini",
    ".mypy.ini",
    "setup.cfg",
    "pytest.ini",
    "tox.ini",
    ".coveragerc",
}
RULE_MESSAGE = "{name} is a rule file; the loop never changes its own rules, ask the user"
PLUGIN_MESSAGE = (
    "{name} is part of the flow plugin; the loop never changes its own rules, ask the user"
)
GATE_MESSAGE = "{name} sets the lint, type, test or dependency gates; ask the user"


def load_file(name: str, path: Path) -> ModuleType:
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def guarded_module() -> ModuleType:
    return load_file("guarded_paths_under_test", MODULE)


EDIT = load_file("edit_check_guarded_paths", HOOK)


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        check=True,
    )


@pytest.fixture
def lab(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    lab_dir = tmp_path / "lab"
    for rel in (
        "lab/ops/flow.toml",
        "lab/.flow/flow.toml",
        "lab/reviews/views.py",
        "lab/.claude/rules/git.md",
        "lab/pyproject.toml",
        "plugins/agent-flow/hooks/hooks.json",
    ):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("x\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "switch", "-q", "-c", "task/526-x")
    return lab_dir


def check(lab: Path, rel: str, allowed: str = "") -> list[str]:
    env = {**LOOP, "FLOW_ALLOWED_EDITS": allowed} if allowed else dict(LOOP)
    result: list[str] = EDIT.evaluate(str(lab / rel), lab, env, EDIT.real_run, "Edit", {})
    return result


# M1: the module holds the rule once


def test_the_four_sets_hold_exactly_the_names_of_the_rule() -> None:
    """M1."""
    module = guarded_module()
    assert set(module.PROTECTED_DIRS) == {".github", ".claude"}
    assert set(module.PROTECTED_FILES) == {".mcp.json", "flow.toml"}
    assert set(module.PLUGIN_DIRS) == {"plugins", ".claude-plugin"}
    assert set(module.GATE_FILES) == GATE_NAMES


@pytest.mark.parametrize(
    ("parts", "kind"),
    [
        ((".claude", "rules", "git.md"), "rule"),
        (("lab", ".github", "workflows", "checks.yml"), "rule"),
        ((".mcp.json",), "rule"),
        (("ops", "flow.toml"), "rule"),
        ((".flow", "flow.toml"), "rule"),
        (("plugins", "agent-flow", "hooks", "hooks.json"), "plugin"),
        ((".claude-plugin", "marketplace.json"), "plugin"),
        (("pyproject.toml",), "gate"),
        (("uv.lock",), "gate"),
        (("reviews", "conftest.py"), "gate"),
        (("reviews", "services.py"), None),
        (("ops", "agent_tick.py"), None),
        (("lab", "plugins", "x.py"), None),  # plugins counts only as the first folder
    ],
)
def test_guarded_kind_gives_rule_plugin_gate_or_none(
    parts: tuple[str, ...], kind: str | None
) -> None:
    """M1."""
    assert guarded_module().guarded_kind(parts) == kind


def test_guarded_kind_checks_rule_before_plugin_before_gate() -> None:
    """M1: the order of AC1."""
    module = guarded_module()
    assert module.guarded_kind(("plugins", ".claude", "x.md")) == "rule"
    assert module.guarded_kind(("plugins", "flow.toml")) == "rule"
    assert module.guarded_kind(("plugins", "pyproject.toml")) == "plugin"
    assert module.guarded_kind((".claude-plugin", "uv.lock")) == "plugin"


# M2: the hook defines none of it and keeps the messages of main


def test_the_hook_defines_none_of_the_rule_and_reads_guarded_paths() -> None:
    """M2."""
    tree = ast.parse(HOOK.read_text())
    defined: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            defined.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
        elif isinstance(node, ast.FunctionDef | ast.ClassDef):
            defined.add(node.name)
    assert not defined & set(NAMES)
    assert "guarded_paths" in HOOK.read_text()
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
    }
    assert "guarded_kind" in used


@pytest.mark.parametrize(
    ("rel", "message"),
    [
        (".claude/rules/git.md", RULE_MESSAGE.format(name="git.md")),
        ("../plugins/agent-flow/hooks/hooks.json", PLUGIN_MESSAGE.format(name="hooks.json")),
        ("pyproject.toml", GATE_MESSAGE.format(name="pyproject.toml")),
    ],
)
def test_the_refusal_messages_are_those_of_main(lab: Path, rel: str, message: str) -> None:
    """M2: a rule file, a plugin file and a gate file."""
    assert check(lab, rel) == [message]


def test_a_listed_guarded_file_is_still_allowed(lab: Path) -> None:
    """M2: the FLOW_ALLOWED_EDITS allow stays."""
    assert check(lab, "pyproject.toml", "pyproject.toml\n") == []


def test_a_rule_that_cannot_answer_refuses_the_edit(
    lab: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M2: fails closed when guarded_kind raises or the module was not loaded."""

    def broken(parts: tuple[str, ...]) -> str | None:
        raise ValueError("broken rule")

    rule = ModuleType("guarded_paths_broken")
    rule.guarded_kind = broken  # type: ignore[attr-defined]
    monkeypatch.setattr(EDIT, "RULE", rule)
    assert check(lab, "reviews/views.py") == [
        "views.py not checked: guarded_paths.py could not answer (broken rule)"
    ]
    monkeypatch.setattr(EDIT, "RULE", None)
    monkeypatch.setattr(EDIT, "RULE_ERROR", "gone")
    assert check(lab, "reviews/views.py") == [
        "views.py not checked: guarded_paths.py could not be loaded (gone)"
    ]
    assert check(lab, "reviews/views.py", "reviews/views.py\n") == []


# M3: flow.toml is a rule file


@pytest.mark.parametrize("rel", ["ops/flow.toml", ".flow/flow.toml"])
def test_an_unlisted_flow_toml_is_refused_as_a_rule_file(lab: Path, rel: str) -> None:
    """M3."""
    expected = "flow.toml is a rule file; the loop never changes its own rules, ask the user"
    assert check(lab, rel, "reviews/views.py\n") == [expected]


@pytest.mark.parametrize("rel", ["ops/flow.toml", ".flow/flow.toml"])
def test_a_listed_flow_toml_may_be_edited(lab: Path, rel: str) -> None:
    """M3."""
    assert check(lab, rel, f"{rel}\n") == []
