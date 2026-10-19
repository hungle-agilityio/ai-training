#!/usr/bin/env python3
"""Drive the app in a headless browser and report what a user would see.

Usage: uv run python .claude/skills/check-in-browser/browser_check.py [--spec FILE] [--out DIR]

It starts the app on a throw-away demo database (never the developer database), opens each
step of the spec in a headless Chromium, saves one screenshot per step, and records console
messages, JavaScript errors and failed network requests. It writes result.json next to the
screenshots and prints a short summary.

Exit code: 0 clean, 1 something is wrong (console error, failed request, missing text, a step
that stopped), 2 the check could not run (NOT CONFIGURED, for example no browser installed).
"""

from __future__ import annotations

import argparse
import json
import os
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


def summarize(steps: list[dict[str, Any]], stopped: str | None) -> dict[str, Any]:
    errors = sum(len(step["console_errors"]) + len(step["page_errors"]) for step in steps)
    failures = sum(len(step["network_failures"]) for step in steps)
    wrong = sum(len(step["problems"]) for step in steps)
    clean = errors == 0 and failures == 0 and wrong == 0 and stopped is None
    return {
        "steps": steps,
        "console_errors": errors,
        "network_failures": failures,
        "problems": wrong,
        "stopped": stopped,
        "status": "clean" if clean else "not clean",
    }


def run_step(
    page: Any, base: str, step: dict[str, Any], out_dir: Path, index: int
) -> tuple[dict[str, Any], bool]:
    """Run one step; the second value is False when an action failed."""
    record: dict[str, Any] = {
        "name": step["name"],
        "console_errors": [],
        "console_warnings": [],
        "page_errors": [],
        "network_failures": [],
        "problems": [],
    }
    page.on(
        "console",
        lambda m: (
            record["console_errors" if m.type == "error" else "console_warnings"].append(m.text)
            if m.type in ("error", "warning")
            else None
        ),
    )
    page.on("pageerror", lambda e: record["page_errors"].append(str(e)))
    page.on(
        "response",
        lambda r: (
            record["network_failures"].append(f"{r.status} {r.url}")
            if r.status >= 400 and not r.url.endswith("favicon.ico")
            else None
        ),
    )
    page.on("requestfailed", lambda r: record["network_failures"].append(f"failed {r.url}"))
    ok = True
    try:
        if "goto" in step:
            page.goto(base + step["goto"], wait_until="load", timeout=15000)
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
        record["problems"].append(f"action failed: {str(error).splitlines()[0]}")
    file = out_dir / f"{index:02d}-{step['name']}.png"
    page.screenshot(path=str(file), full_page=True)
    record.update(
        {"url": page.url.replace(base, ""), "title": page.title(), "screenshot": file.name}
    )
    record["problems"] += judge(step, page.inner_text("body"))
    return record, ok


def run(root: Path, steps: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix="browser-check-"))
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    server = start_app(root, temp / "demo.sqlite3", port)
    try:
        if not wait_until_ready(base + "/dashboard/"):
            raise RuntimeError("the app did not start")
        results: list[dict[str, Any]] = []
        failed_in_a_row = 0
        stopped: str | None = None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(
                viewport=VIEWPORT, locale="en-US", timezone_id="Asia/Ho_Chi_Minh"
            )
            for index, step in enumerate(steps, 1):
                page = context.new_page()
                record, ok = run_step(page, base, step, out_dir, index)
                page.close()
                results.append(record)
                failed_in_a_row = 0 if ok else failed_in_a_row + 1
                if failed_in_a_row >= MAX_FAILED_ACTIONS:
                    stopped = (
                        f"stopped after {MAX_FAILED_ACTIONS} failed actions in a row: ask the user"
                    )
                    break
            browser.close()
        summary = summarize(results, stopped)
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
        mark = "OK " if not flags else "BAD"
        print(f"{mark} {step['name']:<12} {step['url']:<28} {step['screenshot']}")
        for flag in flags:
            print(f"      - {flag}")
    print(
        f"console: {summary['console_errors']} error(s), "
        f"network: {summary['network_failures']} failure(s), "
        f"checks: {summary['problems']} problem(s)"
    )
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
    args = parser.parse_args(argv)
    root = project_root(Path.cwd())
    out_dir = args.out or root / "out" / "browser-check" / datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        summary = run(root, load_steps(args.spec), out_dir)
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
    return 0 if summary["status"] == "clean" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
