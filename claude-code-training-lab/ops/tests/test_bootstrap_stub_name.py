"""The bootstrap template test is not collected by `pytest ops`. Run: pytest ops/tests"""

from __future__ import annotations

import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

from ops import bootstrap

APP = Path(__file__).resolve().parents[2]


def test_no_stub_file_looks_like_a_test() -> None:
    names = [path.name for path in bootstrap.STUBS.iterdir() if path.is_file()]
    assert not [name for name in names if fnmatch(name, "test_*.py")]
    assert (bootstrap.STUBS / "test_flow_config.py.stub").is_file()


def test_bootstrap_still_writes_the_flow_config_test_under_its_test_name() -> None:
    assert bootstrap.FLOW_TEST_STUB == "test_flow_config.py.stub"
    assert bootstrap.FLOW_TEST_NAME == "test_flow_config.py"


def test_pytest_ops_collects_nothing_under_bootstrap_stubs() -> None:
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "ops", "--collect-only", "-q", "--no-cov",
         "-p", "no:cacheprovider"],
        cwd=APP, capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert "ops/bootstrap_stubs/" not in done.stdout
