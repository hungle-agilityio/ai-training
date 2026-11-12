"""Accessibility scan of the main screens with axe-core, light and dark (ADR-032)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

APP = Path(__file__).resolve().parents[1]
AXE_PATH = Path(__file__).resolve().parent / "vendor" / "axe.min.js"
AXE_SHA256 = "880970c081707360e64f34cea25ff91892f5bc95675b0776925b9709dd8a68bb"
AXE_MISMATCH = "axe.min.js does not match axe-core 4.10.3"
BROWSER_CHECK_PATH = APP / ".claude" / "skills" / "check-in-browser" / "browser_check.py"
SCHEMES = ("light", "dark")
BLOCKING = ("serious", "critical")
LOGIN_STEP = {"name": "login", "goto": "/login/"}
NOT_OPENED = "could not open the page"
AXE_RUN = "() => axe.run(document, {resultTypes: ['violations']})"


def load_browser_check() -> Any:
    """The browser check is a skill script, not a package: it is loaded by its path."""
    spec = importlib.util.spec_from_file_location("browser_check", BROWSER_CHECK_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {BROWSER_CHECK_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


browser_check: Any = load_browser_check()


class CouldNotRun(RuntimeError):
    """The scan could not go on: no app, no browser or no sign-in."""


def first_line(error: BaseException) -> str:
    lines = str(error).splitlines()
    return lines[0] if lines else type(error).__name__


def first_target(violation: dict[str, Any]) -> str:
    nodes = violation.get("nodes") or []
    target = (nodes[0].get("target") or [""]) if nodes else [""]
    first = target[0]
    return " ".join(str(part) for part in first) if isinstance(first, list) else str(first)


def report_lines(name: str, scheme: str, violations: list[dict[str, Any]]) -> list[str]:
    """Serious and critical findings fail the step, the others are notes; PASS needs no FAIL."""
    lines: list[str] = []
    failed = False
    for violation in violations:
        count = len(violation.get("nodes") or [])
        if violation.get("impact") in BLOCKING:
            failed = True
            target = first_target(violation)
            lines.append(f"FAIL {name} {scheme}: {violation['id']} x{count} ({target})")
        else:
            lines.append(f"NOTE {name} {scheme}: {violation['id']} x{count}")
    if not failed:
        lines.append(f"PASS {name} {scheme}")
    return lines


def result_line(lines: list[str]) -> tuple[str, int]:
    """The last line and the exit code: every FAIL line is one failure."""
    failures = sum(1 for line in lines if line.startswith("FAIL "))
    if failures:
        return f"result: {failures} failures", 1
    return "result: clean", 0


def axe_matches() -> bool:
    try:
        digest = hashlib.sha256(AXE_PATH.read_bytes()).hexdigest()
    except OSError:
        return False
    return digest == AXE_SHA256


def scan_step(page: Any, base: str, step: dict[str, Any], scheme: str, axe: str) -> list[str]:
    """Open the step as the browser check does, then run axe on the page it ends on."""
    name = str(step["name"])
    try:
        if "goto" in step:
            response = page.goto(base + step["goto"], wait_until="load", timeout=15000)
            if response is not None and response.status >= 400:
                return [f"FAIL {name} {scheme}: {NOT_OPENED}"]
        for action in step.get("actions", []):
            if "select" in action:
                for selector, value in action["select"].items():
                    page.select_option(selector, value, timeout=5000)
            if "fill" in action:
                for selector, value in action["fill"].items():
                    page.fill(selector, value, timeout=5000)
            if "click" in action:
                with page.expect_navigation(wait_until="load", timeout=8000):
                    page.click(action["click"], timeout=5000)
    except Exception:  # a page that cannot be opened is a failure of that step, not of the run
        return [f"FAIL {name} {scheme}: {NOT_OPENED}"]
    page.add_script_tag(content=axe)
    found = page.evaluate(AXE_RUN)
    return report_lines(name, scheme, list(found.get("violations") or []))


def scan_scheme(
    browser: Any, base: str, password: str, steps: list[dict[str, Any]], scheme: str, axe: str
) -> list[str]:
    context = browser.new_context(
        color_scheme=scheme,
        viewport=browser_check.VIEWPORT,
        locale="en-US",
        timezone_id="Asia/Ho_Chi_Minh",
    )
    lines: list[str] = []
    try:
        page = context.new_page()
        lines += emit(scan_step(page, base, LOGIN_STEP, scheme, axe))
        try:
            browser_check.sign_in(page, base, password)
        except Exception as error:
            raise CouldNotRun(first_line(error)) from error
        finally:
            page.close()
        for step in steps:
            page = context.new_page()
            try:
                lines += emit(scan_step(page, base, step, scheme, axe))
            finally:
                page.close()
    finally:
        context.close()
    return lines


def emit(lines: list[str]) -> list[str]:
    for line in lines:
        print(line, flush=True)
    return lines


def scan(steps: list[dict[str, Any]], schemes: tuple[str, ...]) -> list[str]:
    """Start the app on a throw-away demo database and scan every step in every scheme."""
    from playwright.sync_api import sync_playwright

    axe = AXE_PATH.read_text()
    temp = Path(tempfile.mkdtemp(prefix="a11y-check-"))
    port = browser_check.free_port()
    base = f"http://127.0.0.1:{port}"
    password = browser_check.one_run_secret()
    server = browser_check.start_app(APP, temp / "demo.sqlite3", port, password=password)
    lines: list[str] = []
    try:
        if not browser_check.wait_until_ready(base + "/dashboard/"):
            raise CouldNotRun("the app did not start")
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch()
            except Exception as error:
                raise CouldNotRun(first_line(error)) from error
            try:
                for scheme in schemes:
                    lines += scan_scheme(browser, base, password, steps, scheme, axe)
            finally:
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)
        shutil.rmtree(temp, ignore_errors=True)
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--scheme", choices=[*SCHEMES, "both"], default="both")
    args = parser.parse_args(argv)
    if not axe_matches():
        print(AXE_MISMATCH)
        return 2
    steps = browser_check.load_steps(args.spec)
    schemes = SCHEMES if args.scheme == "both" else (args.scheme,)
    try:
        lines = scan(steps, schemes)
    except CouldNotRun as error:
        print(f"could not run: {error}", file=sys.stderr)
        return 2
    last, code = result_line(lines)
    print(last)
    return code


if __name__ == "__main__":
    sys.exit(main())
