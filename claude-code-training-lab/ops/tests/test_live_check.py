"""Live check after a release (rows M4 to M15b). Run: pytest ops/tests/test_live_check.py --no-cov

No test reaches the network: the HTTP client is a fake, the clock and sleep are fakes. M10 to M12
drive a real headless Chromium against pytest-django's `live_server` and skip when Chromium is
not installed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright import sync_api
from playwright.sync_api import Page, sync_playwright

from ops import flow_config, live_check

OPS = Path(__file__).resolve().parents[1]
PROJECT = OPS.parent
README = OPS / "README.md"
ENV_EXAMPLE = OPS / "agent.env.example"
PASSWORD = "s3cret-pw-Zq9"
FULL_COMMIT = "5213e39" + "a" * 33
OLD_COMMIT = "d7738b4" + "b" * 33

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
setup_command = ["uv", "sync", "--frozen"]
alone_words = []

[checks]
commands = [["uv", "run", "pytest"]]
ci_workflow = "CI"
protected_test_dirs = ["tests"]

[release]
timezone = "Europe/Berlin"
deploy_line = ""
"""
LIVE_DEFAULTS = {
    "url": '"https://shop.example/"',
    "username": '"demo"',
    "wait_minutes": "15",
    "load_warn_seconds": "3",
    "persistent_database": "false",
}

Fetch = Callable[[str, float], live_check.Answer]


def head_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def write_config(tmp_path: Path, with_live: bool = True, **overrides: str | None) -> Path:
    """A flow.toml; an override of None drops that key of [live]."""
    text = VALID
    if with_live:
        values = {**LIVE_DEFAULTS, **overrides}
        body = "".join(f"{key} = {value}\n" for key, value in values.items() if value is not None)
        text += f"\n[live]\n{body}"
    path = tmp_path / "flow.toml"
    path.write_text(text, encoding="utf-8")
    return path


def live_config(url: str = "https://shop.example") -> flow_config.LiveConfig:
    return flow_config.LiveConfig(
        url=url,
        username="demo",
        wait_minutes=15,
        load_warn_seconds=3,
        persistent_database=False,
    )


# ---------------------------------------------------------------- fakes


class FakeTime:
    """One fake world: sleep and every fake request move the same clock."""

    def __init__(self, per_request: float = 0.2) -> None:
        self.now = 0.0
        self.per_request = per_request
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class StepClock:
    """Returns the current time, then moves it by the next increment (so two reads = one step).

    Increments come in pairs so that a step is timed right even if one extra read comes first.
    Until `armed` is True the time stands still.
    """

    def __init__(self, increments: list[float], armed: bool = True) -> None:
        self.now = 0.0
        self.increments = increments
        self.index = 0
        self.armed = armed

    def __call__(self) -> float:
        if not self.armed:
            return self.now
        value = self.now
        self.now += self.increments[min(self.index, len(self.increments) - 1)]
        self.index += 1
        return value


class Poller:
    """A fake `fetch` that gives the next answer of a list each time and remembers the calls."""

    def __init__(self, answers: list[live_check.Answer], world: FakeTime) -> None:
        self.answers = answers
        self.world = world
        self.calls: list[tuple[str, float, float]] = []

    def __call__(self, url: str, timeout: float) -> live_check.Answer:
        self.calls.append((url, timeout, self.world.now))
        answer = self.answers[min(len(self.calls) - 1, len(self.answers) - 1)]
        self.world.now += self.world.per_request
        return answer


def answer(status: int | None, **headers: str) -> live_check.Answer:
    return live_check.Answer(
        status=status, headers={k.replace("_", "-"): v for k, v in headers.items()}
    )


def secure_routes(base: str, commit: str = FULL_COMMIT) -> dict[str, live_check.Answer]:
    """The answers of a healthy site, keyed by the exact URL."""
    netloc = urlsplit(base).netloc
    return {
        f"http://{netloc}/dashboard/": answer(301, location=f"https://{netloc}/dashboard/"),
        f"{base}/login/": answer(
            200, x_frame_options="DENY", strict_transport_security="max-age=31536000"
        ),
        f"{base}/dashboard/": answer(302, location="/login/?next=/dashboard/"),
        f"{base}/healthz/": answer(200, x_commit=commit),
    }


class Site:
    """A fake `fetch` over a table of routes; `on_healthz` runs when the health URL is asked."""

    def __init__(
        self, routes: dict[str, live_check.Answer], on_healthz: Callable[[], None] | None = None
    ) -> None:
        self.routes = routes
        self.on_healthz = on_healthz
        self.calls: list[tuple[str, float]] = []

    def __call__(self, url: str, timeout: float) -> live_check.Answer:
        self.calls.append((url, timeout))
        if url.endswith("/healthz/") and self.on_healthz is not None:
            self.on_healthz()
        return self.routes.get(url, answer(404))


def never_fetch(url: str, timeout: float) -> live_check.Answer:
    raise AssertionError(f"no request expected, got {url}")


@pytest.fixture
def no_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("a browser was started")

    monkeypatch.setattr(sync_api, "sync_playwright", boom)
    monkeypatch.setattr(live_check, "sync_playwright", boom, raising=False)


# ---------------------------------------------------------------- M4, M5: the [live] table


def test_committed_flow_file_has_the_live_table() -> None:  # M4
    live = flow_config.load(OPS / "flow.toml").live
    assert live == flow_config.LiveConfig(
        url="https://reviewradar.onrender.com",
        username="demo",
        wait_minutes=15,
        load_warn_seconds=3,
        persistent_database=False,
    )
    assert type(live.persistent_database) is bool
    assert type(live.wait_minutes) is int


def test_live_table_comes_after_release_in_the_committed_file() -> None:  # M4
    text = (OPS / "flow.toml").read_text(encoding="utf-8")
    assert text.index("[release]") < text.index("[live]")


def test_live_url_is_stored_without_trailing_slash(tmp_path: Path) -> None:  # M4
    live = flow_config.load(write_config(tmp_path)).live
    assert live is not None
    assert live.url == "https://shop.example"


def test_lookup_prints_live_values_from_the_command_line(tmp_path: Path) -> None:  # M4
    path = OPS / "flow.toml"
    env = {**os.environ, "FLOW_CONFIG": str(path)}

    def lookup(key: str) -> str:
        done = subprocess.run(
            [sys.executable, str(OPS / "flow_config.py"), key],
            capture_output=True,
            text=True,
            env=env,
        )
        assert done.returncode == 0, done.stderr
        return done.stdout.strip()

    assert lookup("live.url") == "https://reviewradar.onrender.com"
    assert lookup("live.wait_minutes") == "15"
    assert lookup("live.persistent_database") == "false"


def test_lookup_without_live_table_stops_with_exit_2(tmp_path: Path) -> None:  # M5
    path = write_config(tmp_path, with_live=False)
    env = {**os.environ, "FLOW_CONFIG": str(path)}
    done = subprocess.run(
        [sys.executable, str(OPS / "flow_config.py"), "live.url"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert done.returncode == 2
    assert f"{path}: no [live] table" in done.stderr


def test_file_without_live_table_loads_with_live_none(tmp_path: Path) -> None:  # M5
    assert flow_config.load(write_config(tmp_path, with_live=False)).live is None


def test_live_table_without_url_stops_naming_the_key(tmp_path: Path) -> None:  # M5
    with pytest.raises(flow_config.FlowConfigError, match=r"missing live\.url"):
        flow_config.load(write_config(tmp_path, url=None))


@pytest.mark.parametrize("value", ['"15"', "true", "0", "1.5"])
def test_wait_minutes_must_be_a_whole_number(tmp_path: Path, value: str) -> None:  # M5
    with pytest.raises(flow_config.FlowConfigError) as error:
        flow_config.load(write_config(tmp_path, wait_minutes=value))
    assert "live.wait_minutes must be a whole number" in str(error.value)


def test_persistent_database_must_be_true_or_false(tmp_path: Path) -> None:  # M5
    with pytest.raises(flow_config.FlowConfigError) as error:
        flow_config.load(write_config(tmp_path, persistent_database='"no"'))
    assert "live.persistent_database must be a true or false" in str(error.value)


def test_unknown_live_key_is_refused(tmp_path: Path) -> None:  # M5
    path = write_config(tmp_path)
    path.write_text(path.read_text(encoding="utf-8") + "colour = 1\n", encoding="utf-8")
    with pytest.raises(flow_config.FlowConfigError, match=r"unknown live\.colour"):
        flow_config.load(path)


# ---------------------------------------------------------------- M6, M15b: text files


def test_agent_env_example_ends_with_the_three_live_variables() -> None:  # M6
    lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    for name in ("LIVE_CHECK_PASSWORD", "RENDER_API_KEY", "RENDER_SERVICE_ID"):
        index = lines.index(f"{name}=")
        assert lines[index - 1].startswith("#"), name
        assert len(lines[index - 1]) > 2, name
    order = [lines.index(f"{n}=") for n in ("LIVE_CHECK_PASSWORD", "RENDER_API_KEY")]
    assert order == sorted(order)
    assert [line for line in lines if line.strip()][-1] == "RENDER_SERVICE_ID="


def test_readme_has_a_live_check_section_after_release() -> None:  # M15b
    text = README.read_text(encoding="utf-8")
    assert "\n## Release\n" in text
    assert "\n## Live check\n" in text
    assert text.index("\n## Release\n") < text.index("\n## Live check\n")
    section = text.split("\n## Live check\n", 1)[1].split("\n## ", 1)[0]
    assert "LIVE_CHECK_PASSWORD" in section
    assert "[live]" in section
    assert "result: pass" in section


# ---------------------------------------------------------------- M7: settings and refusals


def test_state_folder_prefers_flow_home_then_the_config(tmp_path: Path) -> None:  # M7
    config = flow_config.load(OPS / "flow.toml")
    assert live_check.state_folder(config, {"FLOW_HOME": str(tmp_path)}) == tmp_path
    assert live_check.state_folder(config, {"FLOW_HOME": ""}) == config.loop_state_dir
    assert live_check.state_folder(config, {}) == config.loop_state_dir


def test_load_settings_reads_the_file_and_the_environment_wins(tmp_path: Path) -> None:  # M7
    if (OPS / "agent.env").exists():
        pytest.skip("ops/agent.env exists here and would be read first")
    (tmp_path / "agent.env").write_text(
        "# comment\nA='x'\nno equals sign\n\n B = \"y\" \nC=file\n", encoding="utf-8"
    )
    config = flow_config.load(OPS / "flow.toml")
    environ = {"FLOW_HOME": str(tmp_path), "C": "env", "D": "new", "B": ""}
    settings = live_check.load_settings(config, environ)
    assert settings["A"] == "x"
    assert settings["B"] == "y"
    assert settings["C"] == "env"
    assert settings["D"] == "new"


def test_no_live_table_exits_2_and_sends_no_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:  # M7
    path = write_config(tmp_path, with_live=False)
    code = live_check.main(
        ["--commit", head_commit()],
        fetch=never_fetch,
        environ={"LIVE_CHECK_PASSWORD": PASSWORD, "FLOW_HOME": str(tmp_path)},
        config_path=path,
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.err.strip() == "no [live] table in flow.toml"
    assert captured.out == ""


def test_blank_password_exits_2_and_sends_no_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:  # M7
    if (OPS / "agent.env").exists():
        pytest.skip("ops/agent.env exists here and would be read first")
    code = live_check.main(
        ["--commit", head_commit()],
        fetch=never_fetch,
        environ={"LIVE_CHECK_PASSWORD": "", "FLOW_HOME": str(tmp_path)},
        config_path=OPS / "flow.toml",
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.err.strip() == "LIVE_CHECK_PASSWORD is not set in agent.env"
    assert "result:" not in captured.out


def test_unknown_commit_exits_2_before_any_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:  # M7
    code = live_check.main(
        ["--commit", "no-such-commit-xyz"],
        fetch=never_fetch,
        environ={"LIVE_CHECK_PASSWORD": PASSWORD, "FLOW_HOME": str(tmp_path)},
        config_path=OPS / "flow.toml",
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.err.strip() == "unknown commit no-such-commit-xyz"


def test_unreadable_flow_config_exits_2_with_its_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:  # M7
    code = live_check.main(
        ["--commit", head_commit()],
        fetch=never_fetch,
        environ={"LIVE_CHECK_PASSWORD": PASSWORD},
        config_path=tmp_path / "missing.toml",
    )
    captured = capsys.readouterr()
    assert code == 2
    assert "missing.toml" in captured.err


@pytest.mark.parametrize("content", [None, "not json", '{"no_steps": []}', '[{"goto": "/"}]'])
def test_unreadable_spec_exits_2_before_any_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: str | None
) -> None:  # M7 (review: a broken spec must not crash after the wait)
    spec = tmp_path / "screens.json"
    if content is not None:
        spec.write_text(content, encoding="utf-8")
    code = live_check.main(
        ["--commit", head_commit()],
        fetch=never_fetch,
        environ={"LIVE_CHECK_PASSWORD": PASSWORD, "FLOW_HOME": str(tmp_path)},
        spec_path=spec,
        config_path=OPS / "flow.toml",
    )
    captured = capsys.readouterr()
    assert code == 2
    assert captured.err.startswith(f"could not read {spec}: ")
    assert len(captured.err.strip().splitlines()) == 1
    assert captured.out == ""


def test_fetch_counts_a_broken_status_line_as_no_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # M8 (review: a malformed answer is "not live yet", never a crash)
    import http.client

    def broken(url: str, timeout: float) -> object:
        raise http.client.BadStatusLine("garbage")

    monkeypatch.setattr(live_check._OPENER, "open", broken)
    assert live_check.fetch("https://shop.example/healthz/", 60) == answer(None)


class TextPage:
    """A fake page for a step with no goto: it only has listeners and a body text."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.visited: list[str] = []

    def on(self, event: str, handler: Callable[[object], None]) -> None:
        pass

    def goto(self, url: str, **kwargs: object) -> None:
        self.visited.append(url)

    def inner_text(self, selector: str) -> str:
        return self.text


def test_a_step_without_goto_checks_the_current_page() -> None:  # M10 (review)
    page = TextPage("Reputation dashboard")
    steps = [{"name": "here", "expect": ["Reputation dashboard"]}]
    clock = StepClock([0.5, 0.5])
    assert live_check.check_steps(page, live_config(), steps, clock) == ["PASS here 0.5s"]
    assert page.visited == []


# ---------------------------------------------------------------- M8, M9: waiting for the commit


def test_wait_prints_live_line_when_third_poll_answers_the_commit() -> None:  # M8
    world = FakeTime()
    poller = Poller(
        [
            answer(200, x_commit=OLD_COMMIT),
            answer(None),
            answer(200, x_commit=FULL_COMMIT),
        ],
        world,
    )
    ok, lines = live_check.wait_until_live(
        live_config(), FULL_COMMIT, poller, world.clock, world.sleep
    )
    assert ok is True
    assert "live: 5213e39 after 0m40s" in lines
    assert world.sleeps == [20, 20]
    assert [(url, timeout) for url, timeout, _ in poller.calls] == [
        ("https://shop.example/healthz/", 60)
    ] * 3


def test_wait_succeeds_at_once_when_first_answer_is_the_commit() -> None:  # M8
    world = FakeTime()
    poller = Poller([answer(200, x_commit=FULL_COMMIT)], world)
    ok, lines = live_check.wait_until_live(
        live_config(), FULL_COMMIT, poller, world.clock, world.sleep
    )
    assert ok is True
    assert world.sleeps == []
    assert any(re.fullmatch(r"live: 5213e39 after 0m0\ds", line) for line in lines)


@pytest.mark.parametrize(
    "not_live",
    [
        answer(200, x_commit=FULL_COMMIT[:7]),
        answer(503, x_commit=FULL_COMMIT),
        answer(200),
    ],
)
def test_wait_needs_status_200_and_the_full_commit(not_live: live_check.Answer) -> None:  # M8
    world = FakeTime()
    poller = Poller([not_live, answer(200, x_commit=FULL_COMMIT)], world)
    ok, _ = live_check.wait_until_live(live_config(), FULL_COMMIT, poller, world.clock, world.sleep)
    assert ok is True
    assert len(poller.calls) == 2


def test_wait_fails_after_15_minutes_and_names_the_commit_still_live() -> None:  # M9
    world = FakeTime()
    poller = Poller([answer(200, x_commit=OLD_COMMIT)], world)
    ok, lines = live_check.wait_until_live(
        live_config(), FULL_COMMIT, poller, world.clock, world.sleep
    )
    assert ok is False
    assert lines[-1] == "FAIL wait: 5213e39 is not live after 15 minutes (live: d7738b4)"
    assert all(started < 900 for _, _, started in poller.calls)
    assert len(poller.calls) >= 40
    assert set(world.sleeps) == {20}


def test_wait_failure_says_none_when_no_answer_had_the_header() -> None:  # M9
    world = FakeTime()
    poller = Poller([answer(None)], world)
    ok, lines = live_check.wait_until_live(
        live_config(), FULL_COMMIT, poller, world.clock, world.sleep
    )
    assert ok is False
    assert lines[-1] == "FAIL wait: 5213e39 is not live after 15 minutes (live: none)"


def test_main_stops_with_fail_when_never_live_and_starts_no_browser(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], no_browser: None
) -> None:  # M9
    commit = head_commit()
    world = FakeTime()
    site = Site({"https://reviewradar.onrender.com/healthz/": answer(200, x_commit=OLD_COMMIT)})

    def fetch(url: str, timeout: float) -> live_check.Answer:
        world.now += world.per_request
        return site(url, timeout)

    code = live_check.main(
        ["--commit", commit],
        fetch=fetch,
        clock=world.clock,
        sleep=world.sleep,
        environ={"LIVE_CHECK_PASSWORD": PASSWORD, "FLOW_HOME": str(tmp_path)},
        config_path=OPS / "flow.toml",
    )
    lines = capsys.readouterr().out.splitlines()
    assert code == 1
    assert f"FAIL wait: {commit[:7]} is not live after 15 minutes (live: d7738b4)" in lines
    assert lines[-1] == "result: fail"


# ---------------------------------------------------------------- M13, M14: security checks


def test_all_five_security_checks_pass_on_a_healthy_site() -> None:  # M13
    site = Site(secure_routes("https://shop.example"))
    lines = live_check.check_security(live_config(), site)
    assert lines == [
        "PASS https-redirect",
        "PASS frame-options",
        "PASS hsts",
        "PASS login-required",
        "PASS healthz",
    ]
    assert {timeout for _, timeout in site.calls} == {60}


def test_https_redirect_check_keeps_the_port_of_the_url() -> None:  # M13
    base = "https://shop.example:8443"
    site = Site(secure_routes(base))
    live_check.check_security(live_config(base), site)
    assert ("http://shop.example:8443/dashboard/", 60) in site.calls


CASES = [
    (
        "http://shop.example/dashboard/",
        answer(200),
        "FAIL https-redirect: got 200",
    ),
    (
        "http://shop.example/dashboard/",
        answer(301, location="http://shop.example/dashboard/"),
        "FAIL https-redirect: Location http://shop.example/dashboard/",
    ),
    (
        "http://shop.example/dashboard/",
        answer(301),
        "FAIL https-redirect: Location none",
    ),
    (
        "http://shop.example/dashboard/",
        answer(None),
        "FAIL https-redirect: got no answer",
    ),
    (
        "https://shop.example/login/",
        answer(200, strict_transport_security="max-age=31536000"),
        "FAIL frame-options: got none",
    ),
    (
        "https://shop.example/login/",
        answer(
            200,
            x_frame_options="DENY",
            strict_transport_security="max-age=31536000; includeSubDomains",
        ),
        "FAIL hsts: got max-age=31536000; includeSubDomains",
    ),
    (
        "https://shop.example/dashboard/",
        answer(200),
        "FAIL login-required: got 200",
    ),
    (
        "https://shop.example/dashboard/",
        answer(302, location="/accounts/login/"),
        "FAIL login-required: Location /accounts/login/",
    ),
    (
        "https://shop.example/healthz/",
        answer(503),
        "FAIL healthz: got 503",
    ),
]


@pytest.mark.parametrize(("url", "bad", "expected"), CASES)
def test_one_failing_security_check_prints_its_reason(
    url: str, bad: live_check.Answer, expected: str
) -> None:  # M14
    routes = secure_routes("https://shop.example")
    routes[url] = bad
    lines = live_check.check_security(live_config(), Site(routes))
    assert expected in lines
    assert len(lines) == 5
    others = [line for line in lines if line != expected]
    assert all(line.startswith("PASS ") for line in others)


def test_security_check_without_a_header_value_says_none_for_hsts() -> None:  # M14
    routes = secure_routes("https://shop.example")
    routes["https://shop.example/login/"] = answer(200, x_frame_options="DENY")
    lines = live_check.check_security(live_config(), Site(routes))
    assert "FAIL hsts: got none" in lines


# ---------------------------------------------------------------- M15: result and secrecy


def test_one_fail_line_gives_result_fail_exit_1_and_never_prints_the_password(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], no_browser: None
) -> None:  # M15
    world = FakeTime()
    code = live_check.main(
        ["--commit", head_commit()],
        fetch=lambda url, timeout: answer(200, x_commit=OLD_COMMIT),
        clock=world.clock,
        sleep=world.sleep,
        environ={"LIVE_CHECK_PASSWORD": PASSWORD, "FLOW_HOME": str(tmp_path)},
        config_path=OPS / "flow.toml",
    )
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out.splitlines()[-1] == "result: fail"
    assert PASSWORD not in captured.out
    assert PASSWORD not in captured.err


# ---------------------------------------------------------------- M10 to M12: a real browser

HOME = {
    "name": "home",
    "goto": "/dashboard/",
    "expect": ["Reputation dashboard"],
}
EMPTY = {
    "name": "empty",
    "goto": "/dashboard/",
    "expect": ["No locations yet"],
}
MISSING_TEXT = "Text that is on no page of the app"


@pytest.fixture(scope="module")
def chromium_installed() -> None:
    try:
        with sync_playwright() as playwright:
            playwright.chromium.launch().close()
    except Exception as error:  # noqa: BLE001
        pytest.skip(f"Chromium is not installed (uv run playwright install chromium): {error}")


@pytest.fixture
def demo_user(django_user_model: type, chromium_installed: None) -> str:
    django_user_model.objects.create_user(username="demo", password=PASSWORD)  # type: ignore[attr-defined]
    return PASSWORD


@contextmanager
def browser_page() -> Iterator[Page]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            yield browser.new_page()
        finally:
            browser.close()


def write_spec(tmp_path: Path, steps: Sequence[Mapping[str, object]]) -> Path:
    path = tmp_path / "screens.json"
    path.write_text(json.dumps({"steps": steps}), encoding="utf-8")
    return path


@pytest.mark.django_db(transaction=True)
def test_step_with_texts_on_the_page_prints_pass(
    live_server: object, demo_user: str, tmp_path: Path
) -> None:  # M10
    live = live_config(live_server.url)  # type: ignore[attr-defined]
    steps = live_check.load_steps(write_spec(tmp_path, [HOME, EMPTY]))
    assert [step["name"] for step in steps] == ["home", "empty"]
    with browser_page() as page:
        assert live_check.sign_in(page, live, demo_user) is None
        lines = live_check.check_steps(page, live, steps, time.monotonic)
    assert len(lines) == 2
    assert re.fullmatch(r"PASS home \d+\.\ds", lines[0]), lines
    assert re.fullmatch(r"PASS empty \d+\.\ds", lines[1]), lines


@pytest.mark.django_db(transaction=True)
def test_step_with_a_missing_text_prints_fail_and_the_next_step_still_runs(
    live_server: object, demo_user: str, tmp_path: Path
) -> None:  # M11
    live = live_config(live_server.url)  # type: ignore[attr-defined]
    bad = {
        "name": "broken",
        "goto": "/dashboard/",
        "expect": ["Reputation dashboard", MISSING_TEXT],
    }
    steps = live_check.load_steps(write_spec(tmp_path, [bad, EMPTY]))
    with browser_page() as page:
        assert live_check.sign_in(page, live, demo_user) is None
        lines = live_check.check_steps(page, live, steps, time.monotonic)
    assert lines[0] == f'FAIL broken: missing text "{MISSING_TEXT}"'
    assert re.fullmatch(r"PASS empty \d+\.\ds", lines[1]), lines


@pytest.mark.django_db(transaction=True)
def test_step_with_an_unknown_page_prints_fail_with_the_http_status(
    live_server: object, demo_user: str, tmp_path: Path
) -> None:  # M11
    live = live_config(live_server.url)  # type: ignore[attr-defined]
    gone = {"name": "gone", "goto": "/no-such-page/", "expect": []}
    steps = live_check.load_steps(write_spec(tmp_path, [gone]))
    with browser_page() as page:
        assert live_check.sign_in(page, live, demo_user) is None
        lines = live_check.check_steps(page, live, steps, time.monotonic)
    assert lines == ["FAIL gone: HTTP 404"]


@pytest.mark.django_db(transaction=True)
def test_sign_in_with_a_wrong_password_returns_the_fail_line(
    live_server: object, demo_user: str
) -> None:  # M11
    live = live_config(live_server.url)  # type: ignore[attr-defined]
    with browser_page() as page:
        assert live_check.sign_in(page, live, "not-the-password") == (
            "FAIL sign-in: could not sign in as demo"
        )


@pytest.mark.django_db(transaction=True)
def test_main_with_a_wrong_password_prints_sign_in_fail_then_result_fail(
    live_server: object,
    demo_user: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:  # M11
    commit = head_commit()
    config = live_server_config(tmp_path, live_server.url)  # type: ignore[attr-defined]
    site = Site(secure_routes(live_server.url, commit))  # type: ignore[attr-defined]
    code = live_check.main(
        ["--commit", commit],
        fetch=site,
        environ={"LIVE_CHECK_PASSWORD": "wrong-password-123", "FLOW_HOME": str(tmp_path)},
        spec_path=write_spec(tmp_path, [HOME, EMPTY]),
        config_path=config,
    )
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert code == 1
    assert "FAIL sign-in: could not sign in as demo" in lines
    assert lines[-1] == "result: fail"
    assert "wrong-password-123" not in captured.out + captured.err


def live_server_config(tmp_path: Path, url: str) -> Path:
    text = (OPS / "flow.toml").read_text(encoding="utf-8")
    replaced = text.replace('url = "https://reviewradar.onrender.com"', f'url = "{url}"')
    assert replaced != text
    path = tmp_path / "live-flow.toml"
    path.write_text(replaced, encoding="utf-8")
    return path


@pytest.mark.django_db(transaction=True)
def test_a_step_that_takes_3_4_seconds_prints_slow_and_still_passes(
    live_server: object, demo_user: str, tmp_path: Path
) -> None:  # M12
    live = live_config(live_server.url)  # type: ignore[attr-defined]
    steps = live_check.load_steps(write_spec(tmp_path, [HOME, EMPTY]))
    clock = StepClock([3.4, 3.4, 0.1, 0.1, 0.1])
    with browser_page() as page:
        assert live_check.sign_in(page, live, demo_user) is None
        lines = live_check.check_steps(page, live, steps, clock)
    assert lines == ["SLOW home 3.4s (over 3s)", "PASS empty 0.1s"]


@pytest.mark.django_db(transaction=True)
def test_a_step_that_takes_3_04_seconds_prints_pass_with_3_0(
    live_server: object, demo_user: str, tmp_path: Path
) -> None:  # M12
    live = live_config(live_server.url)  # type: ignore[attr-defined]
    steps = live_check.load_steps(write_spec(tmp_path, [HOME, EMPTY]))
    clock = StepClock([3.04, 3.04, 0.1, 0.1, 0.1])
    with browser_page() as page:
        assert live_check.sign_in(page, live, demo_user) is None
        lines = live_check.check_steps(page, live, steps, clock)
    assert lines == ["PASS home 3.0s", "PASS empty 0.1s"]


@pytest.mark.django_db(transaction=True)
def test_a_step_that_takes_3_05_seconds_rounds_half_up_to_slow(
    live_server: object, demo_user: str, tmp_path: Path
) -> None:  # M12
    live = live_config(live_server.url)  # type: ignore[attr-defined]
    steps = live_check.load_steps(write_spec(tmp_path, [HOME]))
    readings = iter([0.0, 3.05])
    with browser_page() as page:
        assert live_check.sign_in(page, live, demo_user) is None
        lines = live_check.check_steps(page, live, steps, lambda: next(readings))
    assert lines == ["SLOW home 3.1s (over 3s)"]


@pytest.mark.django_db(transaction=True)
def test_main_with_one_slow_step_ends_with_result_pass_1_slow(
    live_server: object,
    demo_user: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:  # M12
    base: str = live_server.url  # type: ignore[attr-defined]
    commit = head_commit()
    clock = StepClock([3.4, 3.4, 0.1, 0.1, 0.1], armed=False)

    def arm() -> None:
        clock.armed = True

    site = Site(secure_routes(base, commit), on_healthz=arm)
    # live_server is plain http, so the https-redirect URL is the login-required URL too:
    # its first answer is the redirect to https, the next ones the redirect to /login/.
    plain = f"http://{urlsplit(base).netloc}/dashboard/"
    upgrade = answer(301, location=f"https://{urlsplit(base).netloc}/dashboard/")
    asked: list[str] = []

    def fetch(url: str, timeout: float) -> live_check.Answer:
        asked.append(url)
        if url == plain and asked.count(url) == 1:
            return upgrade
        return site(url, timeout)

    code = live_check.main(
        ["--commit", commit],
        fetch=fetch,
        clock=clock,
        sleep=lambda seconds: None,
        environ={"LIVE_CHECK_PASSWORD": demo_user, "FLOW_HOME": str(tmp_path / "home")},
        spec_path=write_spec(tmp_path, [HOME, EMPTY]),
        config_path=live_server_config(tmp_path, base),
    )
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert code == 0, captured.out + captured.err
    assert re.fullmatch(rf"live: {commit[:7]} after \d+m\d\ds", lines[0]), lines
    assert "SLOW home 3.4s (over 3s)" in lines
    assert "PASS empty 0.1s" in lines
    assert lines[-1] == "result: pass, 1 slow"
    assert demo_user not in captured.out + captured.err
