#!/usr/bin/env python3
"""Drive the app in a headless browser and report what a user would see.

Usage: uv run python .claude/skills/check-in-browser/browser_check.py [--spec FILE] [--out DIR]

It starts the app on a throw-away demo database (never the developer database), opens each
step of the spec in a headless Chromium, saves one screenshot per step, and records console
messages, JavaScript errors and failed network requests. It writes result.json next to the
screenshots and prints a short summary.

Every page text, log line and address is scanned for personal data (emails, phone numbers,
tokens, local paths, public IP addresses, credentials in a URL). If anything is found the run stops
at once, the screenshot of that step is not kept, and logs are stored with the values replaced by
[redacted]. Fields marked data-sensitive can be blurred with --blur.

Exit code: 0 clean, 1 something is wrong (console error, failed request, missing text, a step
that stopped), 2 the check could not run (NOT CONFIGURED, for example no browser installed),
3 personal data was found (masking).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

MAX_FAILED_ACTIONS = 3
VIEWPORT = {"width": 1280, "height": 800}
VIEWPORT_LIMITS = (200, 4000)

DEFAULT_STEPS: list[dict[str, Any]] = [
    {"name": "dashboard", "goto": "/dashboard/", "expect": ["Reputation dashboard", "Riverside"]},
    {"name": "reviews", "goto": "/reviews/", "expect": ["Every customer review", "Friendly staff"]},
    {
        "name": "filter-bad",
        "goto": "/reviews/",
        "actions": [{"select": {"#filter-rating": "bad"}}, {"click": "button[type=submit]"}],
        "expect": ["Waited 50 minutes"],
        "absent": ["Friendly staff"],
    },
    {
        "name": "filter-good",
        "goto": "/reviews/",
        "actions": [{"select": {"#filter-rating": "good"}}, {"click": "button[type=submit]"}],
        "expect": ["Friendly staff"],
        "absent": ["Waited 50 minutes"],
    },
    {
        "name": "no-match",
        "goto": "/reviews/",
        "actions": [{"fill": {"#filter-week": "2001-01-01"}}, {"click": "button[type=submit]"}],
        "expect": ["No reviews found"],
    },
]


# ---- masking: personal data must never be left in a screenshot, a log or a report

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
LOCAL_PATH = re.compile(r"/(?:Users|home)/[\w.-]+|[A-Za-z]:\\Users\\[\w.-]+")
URL_CREDENTIALS = re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
PHONE = re.compile(r"(?<![\w.])\+?\(?\d[\d ()./-]{7,}\d(?![\w])")
BLUR_CSS = "[data-sensitive]{filter:blur(6px) !important;}"
REDACTED = "[redacted]"


def secret_pattern() -> re.Pattern[str]:
    path = Path(__file__).resolve().parents[2] / "hooks" / "before-commit-check.py"
    spec = importlib.util.spec_from_file_location("commit_hook", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pattern: re.Pattern[str] = module.SECRET
    return pattern


def phone_numbers(text: str) -> list[str]:
    found: list[str] = []
    for match in PHONE.finditer(text):
        value = match.group(0)
        digits = re.sub(r"\D", "", value)
        has_separator = value.startswith("+") or re.search(r"[ ()./-]", value) is not None
        is_date = re.match(r"\d{4}-\d{2}-\d{2}", value) is not None
        if has_separator and not is_date and 9 <= len(digits) <= 15:
            found.append(value)
    return found


def public_addresses(text: str) -> list[str]:
    found: list[str] = []
    for match in IPV4.finditer(text):
        octets = [int(part) for part in match.group(0).split(".")]
        loopback = octets[0] == 127 or octets == [0, 0, 0, 0]
        if all(part <= 255 for part in octets) and not loopback:
            found.append(match.group(0))
    return found


def scan_text(text: str) -> list[str]:
    """The kinds of personal data in a text (never the values)."""
    checks = (
        ("email", bool(EMAIL.search(text))),
        ("phone number", bool(phone_numbers(text))),
        ("token", bool(secret_pattern().search(text))),
        ("local path", bool(LOCAL_PATH.search(text))),
        ("ip address", bool(public_addresses(text))),
        ("credentials in a url", bool(URL_CREDENTIALS.search(text))),
    )
    return [name for name, present in checks if present]


def redact(text: str) -> str:
    """The text with every value that scan_text would find replaced by [redacted]."""
    for pattern in (secret_pattern(), URL_CREDENTIALS, EMAIL, LOCAL_PATH):
        text = pattern.sub(REDACTED, text)
    for value in phone_numbers(text) + public_addresses(text):
        text = text.replace(value, REDACTED)
    return text


def masking_of(steps: list[dict[str, Any]]) -> dict[str, Any]:
    findings = [
        {"step": step["name"], "kinds": step["masking_findings"]}
        for step in steps
        if step.get("masking_findings")
    ]
    return {"status": "findings" if findings else "clean", "findings": findings}


def project_root(start: Path) -> Path:
    for folder in (start, *start.parents):
        if (folder / "manage.py").is_file():
            return folder
    return start


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_until_ready(url: str, seconds: float = 30.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def start_app(root: Path, database: Path, port: int) -> subprocess.Popen[bytes]:
    env = {**os.environ, "DJANGO_DB_NAME": str(database), "DJANGO_DEBUG": "1"}
    for command in (["migrate", "--noinput"], ["seed_demo_data"]):
        subprocess.run(
            [sys.executable, "manage.py", *command],
            cwd=root,
            env=env,
            check=True,
            capture_output=True,
        )
    return subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        cwd=root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def load_steps(spec: Path | None) -> list[dict[str, Any]]:
    if spec is None:
        return DEFAULT_STEPS
    data = json.loads(spec.read_text())
    steps = data["steps"] if isinstance(data, dict) else data
    if not isinstance(steps, list) or not all("name" in step for step in steps):
        raise ValueError("the spec must be a list of steps, each with a name")
    return list(steps)


def judge(step: dict[str, Any], text: str) -> list[str]:
    """Problems of one step, from the text that the page showed."""
    problems = [
        f"expected text not shown: {item}" for item in step.get("expect", []) if item not in text
    ]
    problems += [
        f"text that must be absent is shown: {item}"
        for item in step.get("absent", [])
        if item in text
    ]
    return problems


def parse_viewport(value: str) -> dict[str, int]:
    """A viewport is <width>x<height>, two whole numbers within VIEWPORT_LIMITS."""
    low, high = VIEWPORT_LIMITS
    width, sep, height = value.lower().partition("x")
    if not (sep and width.isdigit() and height.isdigit()):
        raise ValueError(f"--viewport must be <width>x<height>, for example 390x844, not {value!r}")
    size = {"width": int(width), "height": int(height)}
    if not all(low <= number <= high for number in size.values()):
        raise ValueError(f"--viewport sizes must be from {low} to {high}, not {value!r}")
    return size


def summarize(
    steps: list[dict[str, Any]],
    stopped: str | None,
    masking: dict[str, Any] | None = None,
    viewport: dict[str, int] | None = None,
) -> dict[str, Any]:
    masking = masking or masking_of(steps)
    errors = sum(len(step["console_errors"]) + len(step["page_errors"]) for step in steps)
    failures = sum(len(step["network_failures"]) for step in steps)
    wrong = sum(len(step["problems"]) for step in steps)
    clean = (
        errors == 0
        and failures == 0
        and wrong == 0
        and stopped is None
        and masking["status"] == "clean"
    )
    return {
        "steps": steps,
        "console_errors": errors,
        "network_failures": failures,
        "problems": wrong,
        "stopped": stopped,
        "masking": masking,
        "viewport": viewport or VIEWPORT,
        "status": "clean" if clean else "not clean",
    }


def run_step(
    page: Any, base: str, step: dict[str, Any], out_dir: Path, index: int, blur: bool = False
) -> tuple[dict[str, Any], bool]:
    """Run one step; the second value is False when an action failed."""
    record: dict[str, Any] = {
        "name": step["name"],
        "console_errors": [],
        "console_warnings": [],
        "page_errors": [],
        "network_failures": [],
        "problems": [],
        "masking_findings": [],
    }
    seen: set[str] = set()

    def keep(bucket: str, text: str) -> None:
        seen.update(scan_text(text))
        record[bucket].append(redact(text))

    page.on(
        "console",
        lambda m: (
            keep("console_errors" if m.type == "error" else "console_warnings", m.text)
            if m.type in ("error", "warning")
            else None
        ),
    )
    page.on("pageerror", lambda e: keep("page_errors", str(e)))
    page.on(
        "response",
        lambda r: (
            keep("network_failures", f"{r.status} {r.url}")
            if r.status >= 400 and not r.url.endswith("favicon.ico")
            else None
        ),
    )
    page.on("requestfailed", lambda r: keep("network_failures", f"failed {r.url}"))
    ok = True
    try:
        if "goto" in step:
            response = page.goto(base + step["goto"], wait_until="load", timeout=15000)
            record["http_status"] = response.status if response else None
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
    except Exception as error:  # a failed action is reported, never hidden
        ok = False
        record["problems"].append(f"action failed: {redact(str(error).splitlines()[0])}")
    if blur:
        page.add_style_tag(content=BLUR_CSS)
    file = out_dir / f"{index:02d}-{step['name']}.png"
    page.screenshot(path=str(file), full_page=True)
    body, title, url = page.inner_text("body"), page.title(), page.url.replace(base, "")
    seen.update(scan_text(f"{body}\n{title}\n{url}"))
    record.update({"url": redact(url), "title": redact(title), "screenshot": file.name})
    record["problems"] += [redact(line) for line in judge(step, body)]
    record["masking_findings"] = sorted(seen)
    if seen:
        file.unlink(missing_ok=True)
        record["screenshot"] = ""
    return record, ok


def plant_review(root: Path, database: Path, text: str) -> None:
    """Add one review with this text to the throw-away database (to test the scan only)."""
    code = (
        "import os;from django.utils import timezone;"
        "from reviews.models import Branch, Review;"
        "Review.objects.create(branch=Branch.objects.first(), rating=3, "
        "text=os.environ['PLANT_TEXT'], created_at=timezone.now())"
    )
    env = {**os.environ, "DJANGO_DB_NAME": str(database), "PLANT_TEXT": text}
    subprocess.run(
        [sys.executable, "manage.py", "shell", "-c", code],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
    )


def run(
    root: Path,
    steps: list[dict[str, Any]],
    out_dir: Path,
    blur: bool = False,
    plant: str | None = None,
    viewport: dict[str, int] | None = None,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix="browser-check-"))
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    server = start_app(root, temp / "demo.sqlite3", port)
    try:
        if plant:
            plant_review(root, temp / "demo.sqlite3", plant)
        if not wait_until_ready(base + "/dashboard/"):
            raise RuntimeError("the app did not start")
        results: list[dict[str, Any]] = []
        failed_in_a_row = 0
        stopped: str | None = None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(
                viewport=viewport or VIEWPORT, locale="en-US", timezone_id="Asia/Ho_Chi_Minh"
            )
            for index, step in enumerate(steps, 1):
                page = context.new_page()
                record, ok = run_step(page, base, step, out_dir, index, blur)
                page.close()
                results.append(record)
                if record["masking_findings"]:
                    kinds = ", ".join(record["masking_findings"])
                    stopped = f"masking: {kinds} found in step {step['name']}; the run is stopped"
                    break
                failed_in_a_row = 0 if ok else failed_in_a_row + 1
                if failed_in_a_row >= MAX_FAILED_ACTIONS:
                    stopped = (
                        f"stopped after {MAX_FAILED_ACTIONS} failed actions in a row: ask the user"
                    )
                    break
            browser.close()
        summary = summarize(results, stopped, viewport=viewport or VIEWPORT)
    finally:
        server.terminate()
        server.wait(timeout=10)
        shutil.rmtree(temp, ignore_errors=True)
    (out_dir / "result.json").write_text(json.dumps(summary, indent=2))
    return summary


def print_summary(summary: dict[str, Any], out_dir: Path) -> None:
    for step in summary["steps"]:
        flags = [
            *step["problems"],
            *step["network_failures"],
            *step["console_errors"],
            *step["page_errors"],
        ]
        mark = "OK " if not flags and not step.get("masking_findings") else "BAD"
        shot = step["screenshot"] or "(no screenshot kept)"
        print(f"{mark} {step['name']:<12} {step['url']:<28} {shot}")
        for kind in step.get("masking_findings", []):
            print(f"      - masking: {kind} found on the page or in the logs")
        for flag in flags:
            print(f"      - {flag}")
    print(
        f"console: {summary['console_errors']} error(s), "
        f"network: {summary['network_failures']} failure(s), "
        f"checks: {summary['problems']} problem(s)"
    )
    size = summary.get("viewport") or VIEWPORT
    print(f"viewport: {size['width']}x{size['height']}")
    print(f"masking: {summary['masking']['status']}")
    if summary["stopped"]:
        print(summary["stopped"])
    print(f"result: {summary['status']}   folder: {out_dir}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument(
        "--spec", type=Path, help="JSON file with the steps (default: the reviews pages)"
    )
    parser.add_argument(
        "--out", type=Path, help="folder for the screenshots (default: out/browser-check/<time>)"
    )
    parser.add_argument(
        "--blur",
        action="store_true",
        help="blur the fields marked data-sensitive in the screenshots",
    )
    parser.add_argument("--plant", help="add a review with this text, to test the scan only")
    parser.add_argument(
        "--viewport", help="browser size as <width>x<height>, e.g. 390x844 (default 1280x800)"
    )
    args = parser.parse_args(argv)
    try:
        viewport = parse_viewport(args.viewport) if args.viewport else dict(VIEWPORT)
    except ValueError as error:
        print(f"NOT RUN: {error}")
        return 2
    root = project_root(Path.cwd())
    out_dir = args.out or root / "out" / "browser-check" / datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        summary = run(
            root, load_steps(args.spec), out_dir, args.blur, args.plant, viewport=viewport
        )
    except ImportError:
        print("NOT CONFIGURED: playwright is not installed (run: uv sync)")
        return 2
    except Exception as error:
        text = str(error)
        if "Executable doesn't exist" in text or "playwright install" in text:
            print("NOT CONFIGURED: no browser installed (run: uv run playwright install chromium)")
            return 2
        print(f"NOT RUN: {text.splitlines()[0] if text else type(error).__name__}")
        return 2
    print_summary(summary, out_dir)
    if summary["masking"]["status"] != "clean":
        return 3
    return 0 if summary["status"] == "clean" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
