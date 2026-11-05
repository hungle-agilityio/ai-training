"""Read the project values of the flow from `ops/flow.toml`; a missing value stops with its name.

Spec: specs/flow-bootstrap/spec.md (AC2 to AC4). Shell scripts call
`python3 ops/flow_config.py <section.key>`. Standard library only, no hidden default.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parent / "flow.toml"
ENV_VAR = "FLOW_CONFIG"
STRING = "string"
WORDS = "list of strings"
COMMANDS = "list of lists of strings"

# section -> key -> expected kind; the order is the order of the file.
SCHEMA: dict[str, dict[str, str]] = {
    "project": {
        "repo": STRING,
        "owner": STRING,
        "app_dir": STRING,
        "display_name": STRING,
        "slug": STRING,
    },
    "loop": {
        "state_dir": STRING,
        "tmux_session": STRING,
        "launchd_label": STRING,
        "setup_command": WORDS,
        "alone_words": WORDS,
    },
    "checks": {
        "commands": COMMANDS,
        "ci_workflow": STRING,
        "protected_test_dirs": WORDS,
    },
    "release": {"timezone": STRING, "deploy_line": STRING},
}


class FlowConfigError(Exception):
    """The config file is unreadable or wrong; the message names the file and the key."""


@dataclass(frozen=True)
class FlowConfig:
    project_repo: str
    project_owner: str
    project_app_dir: str
    project_display_name: str
    project_slug: str
    loop_state_dir: Path
    loop_tmux_session: str
    loop_launchd_label: str
    loop_setup_command: tuple[str, ...]
    loop_alone_words: tuple[str, ...]
    checks_commands: tuple[tuple[str, ...], ...]
    checks_ci_workflow: str
    checks_protected_test_dirs: tuple[str, ...]
    release_timezone: str
    release_deploy_line: str


def _is_words(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(word, str) for word in value)


def _has_kind(value: object, kind: str) -> bool:
    if kind == STRING:
        return isinstance(value, str)
    if kind == WORDS:
        return _is_words(value)
    return isinstance(value, list) and all(_is_words(item) for item in value)


def _label(path: Path) -> str:
    """The file as shown in a message: `ops/flow.toml` for the committed file."""
    if path.resolve() == DEFAULT_PATH:
        return f"{DEFAULT_PATH.parent.name}/{DEFAULT_PATH.name}"
    return str(path)


def _read(path: Path) -> dict[str, Any]:
    label = _label(path)
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise FlowConfigError(f"{label}: cannot read ({error.strerror or error})") from error
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise FlowConfigError(f"{label}: not valid TOML ({error})") from error


def _check(data: dict[str, Any], label: str) -> None:
    for section in data:
        if section not in SCHEMA:
            raise FlowConfigError(f"{label}: unknown {section}")
    for section, keys in SCHEMA.items():
        values = data.get(section)
        if not isinstance(values, dict):
            raise FlowConfigError(f"{label}: missing {section}.{next(iter(keys))}")
        for key in values:
            if key not in keys:
                raise FlowConfigError(f"{label}: unknown {section}.{key}")
        for key, kind in keys.items():
            if key not in values:
                raise FlowConfigError(f"{label}: missing {section}.{key}")
            if not _has_kind(values[key], kind):
                raise FlowConfigError(f"{label}: {section}.{key} must be a {kind}")


def load(path: Path | None = None) -> FlowConfig:
    """Read `path`, else the file named by FLOW_CONFIG, else ops/flow.toml next to this module."""
    if path is None:
        named = os.environ.get(ENV_VAR)
        path = Path(named) if named else DEFAULT_PATH
    data = _read(path)
    _check(data, _label(path))
    project, loop, checks, release = (data[s] for s in SCHEMA)
    return FlowConfig(
        project_repo=project["repo"],
        project_owner=project["owner"],
        project_app_dir=project["app_dir"],
        project_display_name=project["display_name"],
        project_slug=project["slug"],
        loop_state_dir=Path(loop["state_dir"]).expanduser(),
        loop_tmux_session=loop["tmux_session"],
        loop_launchd_label=loop["launchd_label"],
        loop_setup_command=tuple(loop["setup_command"]),
        loop_alone_words=tuple(loop["alone_words"]),
        checks_commands=tuple(tuple(command) for command in checks["commands"]),
        checks_ci_workflow=checks["ci_workflow"],
        checks_protected_test_dirs=tuple(checks["protected_test_dirs"]),
        release_timezone=release["timezone"],
        release_deploy_line=release["deploy_line"],
    )


def _words(value: object) -> str:
    if isinstance(value, tuple):
        return " ".join(_words(item) for item in value)
    return str(value)


def lookup(config: FlowConfig, dotted: str, label: str) -> str:
    """The value of `section.key` on one line; a list is space-separated words."""
    section, _, key = dotted.partition(".")
    if key not in SCHEMA.get(section, {}):
        raise FlowConfigError(f"{label}: unknown {dotted}")
    return _words(getattr(config, f"{section}_{key}"))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python3 ops/flow_config.py <section.key>", file=sys.stderr)
        return 2
    named = os.environ.get(ENV_VAR)
    path = Path(named) if named else DEFAULT_PATH
    try:
        print(lookup(load(path), argv[0], _label(path)))
    except FlowConfigError as error:
        print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
