"""The flow is configured for this repository; also keeps `pytest` from finding nothing."""

from ops import flow_config

EXPECTED_REPO = "{repo}"


def test_flow_toml_names_this_repository() -> None:
    assert flow_config.load().project_repo == EXPECTED_REPO
