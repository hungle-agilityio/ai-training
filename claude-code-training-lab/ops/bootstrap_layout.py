"""The stack-agnostic layout that `bootstrap.py --stack <stack>` writes into a new repository.

Spec: specs/project-layout/spec.md (AC16 to AC24). The product's code goes in `src/<feature>/`
with its tests beside it, documents in `docs/`, scripts in `scripts/` and the whole flow (loop
scripts, plugin, flow.toml) in `.flow/`. Standard library only.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

STACKS = ("python", "node", "other")
LAYOUT_STUBS = Path(__file__).resolve().with_name("bootstrap_stubs") / "layout"
LOOP_DIR = ".flow/loop"
PLUGIN_DIR = ".flow/plugin"
PLUGIN_VERSION = "1.0.0"
LOOP_SKIP = (
    "bootstrap",
    "flow.toml",
    "tests",
    "regression_screens.json",
    "vendor",
    "a11y_check",
    "__init__.py",
    "__pycache__",
)
PLUGIN_SKIP = ("tests", "__pycache__", ".pytest_cache")
# Where an entry of the manifest goes in the new layout; None means it is not copied.
MOVES: dict[str, str | None] = {
    "ops": None,
    "CLAUDE.md": None,
    ".claude/knowledge/decisions/": "docs/decisions/",
    "docs/app/templates/": "docs/templates/",
    "specs/": "docs/specs/",
}
# Paths in the copied texts that name the old layout.
TEXT_MOVES = (
    ("ops/flow.toml", ".flow/flow.toml"),
    (".claude/knowledge/decisions", "docs/decisions"),
    ("docs/app/templates", "docs/templates"),
    ("../plugins/agent-flow", PLUGIN_DIR),
    ("plugins/agent-flow", PLUGIN_DIR),
    ("ops/", f"{LOOP_DIR}/"),
    ("reviews/tests/", "tests/"),
    ("reviews/", "src/"),
)
PATHS = {
    "loop_dir": LOOP_DIR,
    "plugin_dir": PLUGIN_DIR,
    "intent_file": "docs/intent/{feature}.md",
    "specs_dir": "docs/specs",
    "spec_pr_dirs": ["docs/intent", "docs/specs", "docs/design"],
    "plans_dir": "docs/plans",
    "decisions_dir": "docs/decisions",
    "templates_dir": "docs/templates",
    "code_dirs": ["src"],
    "flow_dirs": [
        ".flow/",
        ".claude/",
        ".github/",
        "docs/intent/",
        "docs/specs/",
        "docs/design/",
        "scripts/",
    ],
}
SETUP_COMMANDS = {
    "python": ["uv", "sync", "--frozen"],
    "node": ["npm", "ci"],
    "other": ["bash", "scripts/setup.sh"],
}
ALONE_WORDS = {"python": ["migrations/"], "node": ["migrations/"], "other": []}
CI_SETUP = {
    "python": (
        "      - name: Install uv\n"
        "        run: pip install uv\n"
        "      - name: Install the locked dependencies\n"
        "        run: uv sync --frozen\n"
    ),
    "node": (
        "      - uses: actions/setup-node@v4\n"
        "        with:\n"
        '          node-version: "20"\n'
        "      - name: Install the locked dependencies\n"
        "        run: npm ci\n"
    ),
    "other": "      - name: Set up the stack\n        run: bash scripts/setup.sh\n",
}
FOLDER_READMES = {
    "docs/intent/README.md": "One file per idea: the problem, who it is for, what success is.\n",
    "docs/plans/README.md": "The approved plan of each issue, `<number>-<short-description>.md`.\n",
    "docs/design/README.md": (
        "The clickable prototype of the whole app, prototype.html (ADR-030); one file, every "
        "screen and state.\n"
    ),
    "src/README.md": (
        "The product's code, one folder per feature (`src/<feature>/`), its tests in "
        "`src/<feature>/tests/`.\n"
    ),
}
KNOWLEDGE = {
    ".claude/knowledge/KNOWN_PITFALLS.md": "# Known pitfalls\n\nA gotcha that can happen again: "
    "symptom, cause, fix.\n",
    ".claude/knowledge/BUSINESS_RULES.md": "# Business rules\n\nA rule the business confirmed "
    "(Confirmed) or we assumed (Uncertain).\n",
}

Rename = Callable[[str, str], str]


def destination(rel: str) -> str | None:
    """Where a copied file of the manifest goes in the new layout; None when it is not copied."""
    for old, new in MOVES.items():
        if rel == old or rel.startswith(old if old.endswith("/") else old + "/"):
            return None if new is None else new + rel.removeprefix(old)
    return rel


# Spec documents: the intent in docs/intent/, the spec, tasks and design link in docs/specs/.
SPEC_MOVES = (
    (
        "`specs/<feature>/intent.md`, `spec.md` and `tasks.md`",
        "`docs/intent/<feature>.md`, `docs/specs/<feature>/spec.md` and `tasks.md`",
    ),
    ("`specs/`, `docs/learning/`", "`docs/intent/`, `docs/specs/`, `scripts/`"),
    ("`specs/` and `design/`", "`docs/intent/`, `docs/specs/` and `docs/design/`"),
    ("specs/<feature>/intent.md", "docs/intent/<feature>.md"),
    ("design/<feature>/README.md", "docs/specs/<feature>/design.md"),
    ("docs/app/issues", "docs/issues"),
)
BARE_SPECS = re.compile(r"(?<![\w/.-])specs/")
# The app prototype lives in docs/design/, which the spec pull request may change; also in code.
PROTOTYPE_MOVES = (
    ("design/app/prototype.html", "docs/design/prototype.html"),
    ('Path("design") / "app" / "prototype.html"', 'Path("docs") / "design" / "prototype.html"'),
)
# The index of the copied decision records lists exactly the records the copy holds.
INDEX_HEADING = "\n## Index\n"
ADR_FILE = re.compile(r"^ADR-\d{3}-.+\.md$")
INDEX_LINE = re.compile(r"^- \[ADR-\d{3}: .*\]\((?P<file>ADR-\d{3}-[^)]+\.md)\)$")
ADR_HEADING = re.compile(r"^# (?P<number>ADR-\d{3}): (?P<title>.+)$", re.M)


# A new project has one loop variable, FLOW_LOOP, and one home variable, FLOW_HOME; the source
# also accepts its own older names, which a copy has no use for.
LOOP_VARIABLE_MOVES = (
    ("FLOW_LOOP=1 or REVIEWRADAR_LOOP=1", "FLOW_LOOP=1"),
    ("`FLOW_LOOP=1` or `REVIEWRADAR_LOOP=1`", "`FLOW_LOOP=1`"),
    ("`FLOW_LOOP=1` and `REVIEWRADAR_LOOP=1`", "`FLOW_LOOP=1`"),
    ('("FLOW_LOOP", "REVIEWRADAR_LOOP")', '("FLOW_LOOP",)'),
    ('"FLOW_LOOP": "1", "REVIEWRADAR_LOOP": "1"', '"FLOW_LOOP": "1"'),
    ('"-u", "FLOW_LOOP", "-u", "REVIEWRADAR_LOOP"', '"-u", "FLOW_LOOP"'),
    (
        'os.environ.get("FLOW_HOME") or os.environ.get("REVIEWRADAR_HOME") or ',
        'os.environ.get("FLOW_HOME") or ',
    ),
    ("`FLOW_HOME` or `REVIEWRADAR_HOME` override it", "`FLOW_HOME` overrides it"),
    (
        "`FLOW_LOOP=1`, with `REVIEWRADAR_LOOP=1` still set and accepted | Rename only | "
        "Today's hooks, tests and docs keep working",
        "`FLOW_LOOP=1` | A project-specific name | One name for every project",
    ),
    ("`REVIEWRADAR_DEMO_PASSWORD`", "a password variable named after ReviewRadar"),
    ("a `REVIEWRADAR_` name", "a variable named after ReviewRadar"),
    ("REVIEWRADAR_LOOP", "FLOW_LOOP"),
    ("REVIEWRADAR_HOME", "FLOW_HOME"),
)


def one_loop_variable(text: str) -> str:
    for old, new in LOOP_VARIABLE_MOVES:
        text = text.replace(old, new)
    return text


def move_prototype(text: str) -> str:
    for old, new in PROTOTYPE_MOVES:
        text = text.replace(old, new)
    return text


def decisions_index(readme: str, records: dict[str, str]) -> str:
    """After `## Index`, one line per copied record (file name to text), and nothing else."""
    head, found, rest = readme.partition(INDEX_HEADING)
    if not found:
        return readme
    known = {m.group("file"): line for line in rest.splitlines() if (m := INDEX_LINE.match(line))}
    lines = []
    for name in sorted(records):
        line = known.get(name)
        if line is None:
            heading = ADR_HEADING.search(records[name])
            number, title = (
                (heading.group("number"), heading.group("title"))
                if heading
                else (name[:7], name.removesuffix(".md"))
            )
            line = f"- [{number}: {title}]({name})"
        lines.append(line)
    return head + INDEX_HEADING + "\n" + "\n".join(lines) + "\n"


def move_text(text: str) -> str:
    for old, new in SPEC_MOVES:
        text = text.replace(old, new)
    text = BARE_SPECS.sub("docs/specs/", text)
    for old, new in TEXT_MOVES:
        text = text.replace(old, new)
    return text


def _words(items: Sequence[str]) -> str:
    return "[" + ", ".join(json.dumps(item) for item in items) + "]"


def flow_toml(repo: str, owner: str, name: str, slug: str, stack: str) -> str:
    paths = "\n".join(
        f"{key} = {_words(value) if isinstance(value, list) else json.dumps(value)}"
        for key, value in PATHS.items()
    )
    return f"""# The project values of the flow, read by .flow/loop/flow_config.py.

[project]
repo = {json.dumps(repo)}
owner = {json.dumps(owner)}
app_dir = "."
display_name = {json.dumps(name)}
slug = {json.dumps(slug)}

[loop]
state_dir = {json.dumps(f"~/.{slug}")}
tmux_session = {json.dumps(f"{slug}-loop")}
launchd_label = {json.dumps(f"com.{slug}.loop")}
setup_command = {_words(SETUP_COMMANDS[stack])}
alone_words = {_words(ALONE_WORDS[stack])}

[checks]
commands = [["bash", "scripts/check.sh"]]
ci_workflow = "Checks"
protected_test_dirs = ["tests"]

[release]
timezone = "Asia/Ho_Chi_Minh"
deploy_line = ""

[plugin]
id = {json.dumps(f"agent-flow@{slug}")}
marketplace = {json.dumps(slug)}

[paths]
{paths}
"""


def marketplace_json(slug: str, name: str) -> str:
    data = {
        "name": slug,
        "owner": {"name": name},
        "metadata": {"description": f"The agent flow of {name}."},
        "plugins": [
            {
                "name": "agent-flow",
                "source": f"./{PLUGIN_DIR}",
                "description": "The issue-to-pull-request flow: guard hooks, flow skills, "
                "slash commands and sub-agents.",
            }
        ],
    }
    return json.dumps(data, indent=2) + "\n"


def plugin_manifest(text: str, repo: str) -> str:
    data: dict[str, Any] = json.loads(text)
    data["version"] = PLUGIN_VERSION
    data["repository"] = f"https://github.com/{repo}"
    return json.dumps(data, indent=2) + "\n"


# Edit rules of the old layout and of the new one.
EDIT_MOVES = {
    "Edit(./specs/**)": [
        "Edit(./docs/intent/**)",
        "Edit(./docs/specs/**)",
        "Edit(./docs/design/**)",
    ],
    "Edit(./tests/**)": [],
}


def plugin_settings(text: str, repo: str, slug: str) -> str:
    """The plugin comes from this repository's own marketplace (`.claude-plugin/`)."""
    settings: dict[str, Any] = json.loads(text)
    allow: list[str] = settings["permissions"]["allow"]
    moved = [new for rule in allow for new in EDIT_MOVES.get(rule, [rule])]
    settings["permissions"]["allow"] = list(dict.fromkeys(moved))
    settings["extraKnownMarketplaces"] = {slug: {"source": {"source": "github", "repo": repo}}}
    settings["enabledPlugins"] = {f"agent-flow@{slug}": True}
    return json.dumps(settings, indent=2) + "\n"


def stub(stub_file: str, **values: str) -> str:
    text = (LAYOUT_STUBS / stub_file).read_text()
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text


def checks_yml(stack: str) -> str:
    return stub("checks.yml", setup=CI_SETUP[stack].rstrip("\n"))


def gitignore(stack: str) -> str:
    parts = [stub("gitignore-common")]
    if stack in ("python", "node"):
        parts.append(stub(f"gitignore-{stack}"))
    return "\n".join(parts)


def generated(repo: str, owner: str, name: str, slug: str, stack: str) -> dict[str, str]:
    """Every file the layout writes from a stub or from code, by its path in the target."""
    files = {
        "CLAUDE.md": stub("CLAUDE.md", name=name),
        "README.md": stub("README.md", name=name),
        ".env.example": "# Copy to .env and fill in; the real .env is never committed.\n",
        ".gitignore": gitignore(stack),
        ".claude/rules/architecture.md": stub("architecture-rule.md", name=name),
        ".claude/rules/domain.md": (LAYOUT_STUBS.parent / "domain.md")
        .read_text()
        .replace("{name}", name),
        ".claude-plugin/marketplace.json": marketplace_json(slug, name),
        ".flow/flow.toml": flow_toml(repo, owner, name, slug, stack),
        f"{PLUGIN_DIR}/README.md": stub("plugin-README.md", name=name),
        ".github/workflows/checks.yml": checks_yml(stack),
        "docs/architecture.md": stub("architecture.md", name=name),
        "scripts/check.sh": stub(f"check-{stack}.sh"),
        "scripts/setup.sh": stub(f"setup-{stack}.sh"),
        **FOLDER_READMES,
        **KNOWLEDGE,
    }
    if stack == "python":
        files["pyproject.toml"] = stub("pyproject.toml.stub", slug=slug)
    return files


def loop_files(app_root: Path) -> list[tuple[str, Path]]:
    """The loop scripts: what ops/ holds except bootstrap*, flow.toml, tests and the package."""
    found: list[tuple[str, Path]] = []
    ops = app_root / "ops"
    for path in sorted(ops.rglob("*")):
        rel = path.relative_to(ops)
        if not path.is_file() or any(part.lower().startswith(LOOP_SKIP) for part in rel.parts):
            continue
        found.append((f"{LOOP_DIR}/{rel.as_posix()}", path))
    return found


def plugin_files(repo_root: Path) -> list[tuple[str, Path]]:
    """The plugin, without its own tests (they run in the repository it comes from)."""
    plugin = repo_root / "plugins" / "agent-flow"
    found: list[tuple[str, Path]] = []
    for path in sorted(plugin.rglob("*")):
        rel = path.relative_to(plugin)
        skip = (
            any(part in PLUGIN_SKIP for part in rel.parts)
            or rel.name == "conftest.py"
            or rel.as_posix() == "README.md"
        )
        if path.is_file() and not skip:
            found.append((f"{PLUGIN_DIR}/{rel.as_posix()}", path))
    return found
