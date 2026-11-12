"""The flow config has an optional [paths] review_sensitive list; ReviewRadar fills it.

Spec: specs/test-harden/spec.md (AC1, AC2).
Run: pytest ops/tests/test_flow_config_review_sensitive.py
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from ops import flow_config
from ops.flow_config import FlowConfigError

OPS = Path(__file__).resolve().parents[1]
VALID = """\
[project]
repo = "acme/shop"
owner = "acme-owner"
app_dir = "."
display_name = "Shop"
slug = "shop"

[loop]
state_dir = "~/.shop"
tmux_session = "shop-loop"
launchd_label = "com.shop.loop"
setup_command = ["npm", "ci"]
alone_words = []

[checks]
commands = [["bash", "scripts/check.sh"]]
ci_workflow = "Checks"
protected_test_dirs = ["tests"]

[release]
timezone = "Europe/Berlin"
deploy_line = ""
"""
REVIEW_SENSITIVE = [
    "reviews/models.py",
    "reviews/migrations/*",
    "reviews/repositories.py",
    "reviews/*_repository.py",
    "reviews/management/commands/*",
    "reviews/claude_client.py",
    "reviews/templates/registration/*",
    "reviewradar/settings.py",
    "reviewradar/urls.py",
    "../render.yaml",
]


def write_config(folder: Path, paths: str) -> Path:
    path = folder / "flow.toml"
    path.write_text(VALID + paths, encoding="utf-8")
    return path


def test_review_sensitive_list_is_read_as_a_tuple(tmp_path: Path) -> None:
    path = write_config(tmp_path, '\n[paths]\nreview_sensitive = ["reviews/models.py"]\n')
    config = flow_config.load(path)
    assert config.paths_review_sensitive == ("reviews/models.py",)


def test_missing_review_sensitive_key_gives_an_empty_tuple(tmp_path: Path) -> None:
    config = flow_config.load(write_config(tmp_path, ""))
    assert config.paths_review_sensitive == ()


def test_other_paths_keys_without_review_sensitive_give_an_empty_tuple(tmp_path: Path) -> None:
    config = flow_config.load(write_config(tmp_path, '\n[paths]\nloop_dir = "ops"\n'))
    assert config.paths_review_sensitive == ()


def test_path_defaults_hold_an_empty_review_sensitive_list() -> None:
    assert flow_config.PATH_DEFAULTS["review_sensitive"] == []


@pytest.mark.parametrize("value", ["[1]", '"reviews/models.py"', "3"])
def test_a_wrong_review_sensitive_value_names_the_key(tmp_path: Path, value: str) -> None:
    path = write_config(tmp_path, f"\n[paths]\nreview_sensitive = {value}\n")
    with pytest.raises(FlowConfigError) as caught:
        flow_config.load(path)
    assert str(caught.value) == f"{path}: paths.review_sensitive must be a list of strings"


def test_reviewradar_flow_toml_lists_the_ten_sensitive_patterns_in_order() -> None:
    data = tomllib.loads((OPS / "flow.toml").read_text(encoding="utf-8"))
    assert data["paths"]["review_sensitive"] == REVIEW_SENSITIVE


def test_reviewradar_flow_toml_paths_table_has_only_review_sensitive() -> None:
    data = tomllib.loads((OPS / "flow.toml").read_text(encoding="utf-8"))
    assert list(data["paths"]) == ["review_sensitive"]


def test_reviewradar_paths_table_is_the_last_table_of_flow_toml() -> None:
    lines = (OPS / "flow.toml").read_text(encoding="utf-8").splitlines()
    tables = [line.strip() for line in lines if line.startswith("[")]
    assert tables[-1] == "[paths]"


def test_reviewradar_config_loads_the_ten_patterns_and_keeps_the_default_layout() -> None:
    config = flow_config.load(OPS / "flow.toml")
    assert config.paths_review_sensitive == tuple(REVIEW_SENSITIVE)
    assert config.paths_loop_dir == "ops"
