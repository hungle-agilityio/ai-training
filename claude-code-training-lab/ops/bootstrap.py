"""Set up the flow in a clone of a new, empty repository from six values.

Spec: specs/flow-bootstrap/spec.md (AC21 to AC31). It copies what `ops/bootstrap_manifest.toml`
lists, renames it, writes `ops/flow.toml`, stubs, the labels and `agent.env`, and prints the steps
only the owner can do. It never commits, never pushes and runs no `gh` command but
`gh label create`. Standard library only.

    uv run python ops/bootstrap.py --target <folder> --repo <owner/name> --owner <login> \
        --app-dir <folder or .> --name <display name> --slug <slug> --ntfy-topic <topic> \
        [--dry-run] [--no-labels]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().with_name("bootstrap_manifest.toml")
STUBS = Path(__file__).resolve().with_name("bootstrap_stubs")
# The values of this project that the copy renames. Written in two parts so that this file does
# not contain them itself (the copy is checked for old values).
OLD_REPO = "hungle-agilityio/ai-training"
OLD_OWNER = "hungle-agilityio"
OLD_APP_DIR = "claude-code-training-lab"
OLD_NAME = "ReviewRadar"
OLD_TMUX = "rr-loop"

SLUG = re.compile(r"^[a-z][a-z0-9-]{1,30}$")
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ORIGIN = re.compile(
    r"^(?:https?://(?:[^@/]+@)?github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$",
)
FLAGS = (
    ("target", "--target"),
    ("repo", "--repo"),
    ("owner", "--owner"),
    ("app_dir", "--app-dir"),
    ("name", "--name"),
    ("slug", "--slug"),
    ("ntfy_topic", "--ntfy-topic"),
)
COVERAGE_STEP = re.compile(r"^ +- name: Coverage gate.*?(?=^ +- name:|\Z)", re.S | re.M)
CHECKS_COMMANDS = [
    ["uv", "run", "ruff", "check", "."],
    ["uv", "run", "mypy", "."],
    ["uv", "run", "pytest", "-q", "--no-cov", "-p", "no:cacheprovider"],
]
STUB_FILES = (
    ("CLAUDE.md", ".claude/CLAUDE.md"),
    ("architecture.md", ".claude/rules/architecture.md"),
    ("domain.md", ".claude/rules/domain.md"),
)
AGENT_ENV_EXAMPLE = "ops/agent.env.example"


class BootstrapError(Exception):
    """The run cannot go on; the message says why and nothing was written."""


@dataclass(frozen=True)
class Params:
    target: Path
    repo: str
    owner: str
    app_dir: str
    name: str
    slug: str
    ntfy_topic: str
    dry_run: bool
    labels: bool


@dataclass(frozen=True)
class Planned:
    dest: Path
    data: bytes
    mode: int


@dataclass(frozen=True)
class Plan:
    files: tuple[Planned, ...]
    skipped: tuple[str, ...]


def parse(argv: Sequence[str]) -> Params:
    parser = argparse.ArgumentParser(prog="bootstrap.py", description=__doc__.split("\n")[0])
    for _, flag in FLAGS:
        parser.add_argument(flag, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-labels", action="store_true")
    args = parser.parse_args(argv)
    missing = [flag for dest, flag in FLAGS if not getattr(args, dest)]
    if missing:
        raise BootstrapError("missing required flags: " + ", ".join(missing))
    if not SLUG.match(args.slug):
        raise BootstrapError(f"--slug {args.slug!r} must match {SLUG.pattern}")
    if not REPO_NAME.match(args.repo):
        raise BootstrapError(f"--repo {args.repo!r} must look like owner/name")
    app_path = Path(args.app_dir)
    if app_path.is_absolute() or ".." in app_path.parts:
        raise BootstrapError(f"--app-dir {args.app_dir!r} must be a folder inside the repository")
    return Params(
        target=Path(args.target),
        repo=args.repo,
        owner=args.owner,
        app_dir=app_path.as_posix(),
        name=args.name,
        slug=args.slug,
        ntfy_topic=args.ntfy_topic,
        dry_run=args.dry_run,
        labels=not args.no_labels,
    )


def check_target(params: Params) -> None:
    """The target is a git clone whose `origin` is the new repository."""
    target = params.target
    if not target.is_dir() or not (target / ".git").exists():
        raise BootstrapError(f"{target} is not a git clone (no .git); clone the repository first")
    result = subprocess.run(
        ["git", "-C", str(target), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BootstrapError(f"{target} has no remote named origin; it must point at {params.repo}")
    url = result.stdout.strip()
    match = ORIGIN.match(url)
    if match is None or match.group("repo").lower() != params.repo.lower():
        raise BootstrapError(f"origin of {target} is {url}, not {params.repo}")


def source_root() -> Path:
    """The git root of the project this script is copied from."""
    for folder in (APP_ROOT, *APP_ROOT.parents):
        if (folder / ".git").exists():
            return folder
    return APP_ROOT


def _rename(text: str, params: Params) -> str:
    text = text.replace(OLD_REPO, params.repo)
    if params.app_dir == ".":
        text = text.replace(OLD_APP_DIR + "/", "").replace(OLD_APP_DIR, ".")
    else:
        text = text.replace(OLD_APP_DIR, params.app_dir)
    text = text.replace(OLD_NAME, params.name).replace(OLD_TMUX, f"{params.slug}-loop")
    return text.replace(OLD_OWNER, params.owner)


def _transform(rel: str, data: bytes, params: Params) -> bytes:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    if rel.endswith("workflows/checks.yml"):
        text = COVERAGE_STEP.sub("", text)
    text = _rename(text, params)
    if rel.endswith("github-allowed-repo.txt"):
        rest = [line for line in text.splitlines() if line.strip() != params.repo]
        text = "\n".join([params.repo, *rest]) + "\n"
    return text.encode("utf-8")


def _excluded(rel: Path, base: Path, exclude: Sequence[str]) -> bool:
    inside = rel.relative_to(base)
    return bool(set(exclude) & set(inside.parts)) or inside.as_posix() in exclude


def _flow_toml(params: Params) -> str:
    def words(items: Sequence[str]) -> str:
        return "[" + ", ".join(json.dumps(item) for item in items) + "]"

    commands = "\n".join(f"    {words(command)}," for command in CHECKS_COMMANDS)
    return f"""# The project values of the flow, read by ops/flow_config.py. No key has a default.

[project]
repo = {json.dumps(params.repo)}
owner = {json.dumps(params.owner)}
app_dir = {json.dumps(params.app_dir)}
display_name = {json.dumps(params.name)}
slug = {json.dumps(params.slug)}

[loop]
state_dir = {json.dumps(f"~/.{params.slug}")}
tmux_session = {json.dumps(f"{params.slug}-loop")}
launchd_label = {json.dumps(f"com.{params.slug}.loop")}
setup_command = ["uv", "sync", "--frozen"]
alone_words = []

[checks]
commands = [
{commands}
]
ci_workflow = "Checks"
protected_test_dirs = ["tests"]

[release]
timezone = "Asia/Ho_Chi_Minh"
deploy_line = ""
"""


def build_plan(params: Params, manifest: dict[str, Any]) -> Plan:
    root = source_root()
    exclude: list[str] = manifest.get("exclude", [])
    dest_app = params.target if params.app_dir == "." else params.target / params.app_dir
    planned: dict[Path, Planned] = {}
    skipped: list[str] = []
    for entry in manifest["copy"]:
        scope_source = APP_ROOT if entry["scope"] == "app" else root
        scope_dest = dest_app if entry["scope"] == "app" else params.target
        source = scope_source / entry["path"]
        if not source.exists():
            skipped.append(entry["path"])
            continue
        files = (
            [p for p in sorted(source.rglob("*")) if p.is_file()] if source.is_dir() else [source]
        )
        for path in files:
            if _excluded(path, scope_source, exclude):
                continue
            rel = path.relative_to(scope_source).as_posix()
            dest = scope_dest / rel
            planned[dest] = Planned(
                dest, _transform(rel, path.read_bytes(), params), path.stat().st_mode & 0o777
            )
    flow = dest_app / "ops/flow.toml"
    planned[flow] = Planned(flow, _flow_toml(params).encode(), 0o644)
    for stub, rel in STUB_FILES:
        dest = dest_app / rel
        text = (STUBS / stub).read_text().replace("{name}", params.name)
        planned[dest] = Planned(dest, text.encode(), 0o644)
    return Plan(tuple(sorted(planned.values(), key=lambda p: p.dest)), tuple(skipped))


def check_free(plan: Plan, params: Params) -> None:
    taken = [str(p.dest.relative_to(params.target)) for p in plan.files if p.dest.exists()]
    if taken:
        raise BootstrapError(
            "these files already exist, nothing was written:\n  " + "\n  ".join(taken)
        )


def write_files(plan: Plan) -> None:
    for item in plan.files:
        item.dest.parent.mkdir(parents=True, exist_ok=True)
        item.dest.write_bytes(item.data)
        item.dest.chmod(item.mode)


def agent_env_path(params: Params) -> Path:
    return Path.home() / f".{params.slug}" / "agent.env"


def agent_env_text(params: Params) -> str:
    example = (APP_ROOT / AGENT_ENV_EXAMPLE).read_text()
    values = {"AGENT_CONCURRENCY": "1", "NTFY_TOPIC": params.ntfy_topic}
    lines = []
    for line in example.splitlines():
        key = line.split("=", 1)[0]
        lines.append(f"{key}={values[key]}" if "=" in line and key in values else line)
    lines.append("")
    lines.append("# Written by ops/bootstrap.py")
    lines.append("CLAUDE_CODE_ENTRYPOINT=claude-desktop")
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        lines.append(f"CLAUDE_CONFIG_DIR={config_dir}")
    return "\n".join(lines) + "\n"


def write_agent_env(params: Params) -> str:
    path = agent_env_path(params)
    if path.exists():
        return f"{path} exists, kept as it is"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(agent_env_text(params))
    path.chmod(0o600)
    return f"wrote {path}"


def create_labels(params: Params, labels: Sequence[dict[str, str]]) -> list[str]:
    """Run `gh label create` for each label; return the names that failed."""
    failed: list[str] = []
    for label in labels:
        command = [
            "gh", "label", "create", label["name"],
            "--color", label["color"],
            "--description", label["description"].replace(OLD_NAME, params.name),
            "--force", "-R", params.repo,
        ]  # fmt: skip
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError as error:
            print(f"label {label['name']}: cannot run gh ({error})", file=sys.stderr)
            failed.append(label["name"])
            continue
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            print(f"label {label['name']} failed: {detail}", file=sys.stderr)
            failed.append(label["name"])
    return failed


def steps(params: Params) -> list[str]:
    app = "" if params.app_dir == "." else f"{params.app_dir}/"
    return [
        f"Add {params.repo} to the Mac mini fine-grained token and install the Claude GitHub App "
        "on it. Without the token the labels and every loop call fail.",
        "Create the ruleset on main by hand (pull request required, checks must pass).",
        "Run uv sync, then make the first commit and push of main yourself.",
        f"Create a Claude Project, attach {params.repo}, paste "
        f"{app}.claude/project-instructions.md, approve the folder for Remote Control, "
        f"and start Remote Control sessions inside {app or './'}.",
        "Fill in the stubs: .claude/CLAUDE.md, .claude/rules/architecture.md and "
        f".claude/rules/domain.md (each has the line TODO: fill in for {params.name}).",
        "Run bash ops/install-launchd.sh once.",
        f"Subscribe to the ntfy topic {params.ntfy_topic} on your phone.",
        "Keep the total AGENT_CONCURRENCY of all loops on this Mac mini at 2 to 3.",
    ]


def _print_steps(params: Params) -> None:
    print("\nSteps for you:")
    for number, text in enumerate(steps(params), start=1):
        print(f"{number}. {text}")


def run(params: Params) -> int:
    manifest = tomllib.loads(MANIFEST.read_text())
    labels: list[dict[str, str]] = manifest.get("label", [])
    check_target(params)
    plan = build_plan(params, manifest)
    check_free(plan, params)
    verb = "would write" if params.dry_run else "wrote"
    if not params.dry_run:
        write_files(plan)
    for item in plan.files:
        print(f"{verb} {item.dest.relative_to(params.target)}")
    for path in plan.skipped:
        print(f"skipped, not found in the source: {path}")
    if params.dry_run:
        if params.labels:
            print("would create labels: " + ", ".join(label["name"] for label in labels))
        print(f"would write {agent_env_path(params)} unless it exists")
    else:
        if params.labels:
            failed = create_labels(params, labels)
            print(f"labels: {len(labels) - len(failed)} of {len(labels)} created")
            if failed:
                print("labels not created: " + ", ".join(failed))
        print(write_agent_env(params))
    _print_steps(params)
    return 0


def main(argv: Sequence[str]) -> int:
    try:
        return run(parse(argv))
    except BootstrapError as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
