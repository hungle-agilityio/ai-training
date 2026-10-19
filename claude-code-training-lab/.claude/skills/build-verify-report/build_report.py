#!/usr/bin/env python3
"""Run every verify axis and write one report that a person can open and read.

Usage: uv run python .claude/skills/build-verify-report/build_report.py --title "<issue>"
       [--criteria FILE] [--review FILE] [--browser] [--no-open] [--out DIR]

The numbers in the report are read from the real output of each command by this program;
nothing is retyped. It writes report.html (one self-contained page, screenshots embedded) and
report.json to out/verify/<time>/, and opens the page unless --no-open is given.

Exit code: 0 PASS, 1 FAIL, 2 INCOMPLETE (some axis is NOT CONFIGURED, none failed).
"""

from __future__ import annotations

import argparse
import base64
import html
import importlib.util
import json
import re
import subprocess
import sys
import webbrowser
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

Runner = Callable[[list[str], Path], tuple[int, str]]
SKILLS = Path(__file__).resolve().parents[1]
QUERY_ASSERTION = re.compile(r"django_assert_(?:max_)?num_queries|assert(?:Max)?NumQueries", re.I)
TOTAL_COVERAGE = re.compile(r"^TOTAL\s+\d+\s+\d+\s+(\d+)%", re.M)
PASSED = re.compile(r"(\d+) passed")
FAILED = re.compile(r"(\d+) failed")
MYPY_FILES = re.compile(r"no issues found in (\d+) source files?")
STATUSES = ("PASS", "FAIL", "NOT CONFIGURED")


def real_run(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        done = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=900, check=False
        )
    except FileNotFoundError:
        return 127, f"{args[0]}: command not found"
    except subprocess.TimeoutExpired:
        return 124, f"{' '.join(args)}: timed out"
    return done.returncode, done.stdout + done.stderr


def parse_pytest(output: str) -> dict[str, int]:
    passed = PASSED.search(output)
    failed = FAILED.search(output)
    return {
        "passed": int(passed.group(1)) if passed else 0,
        "failed": int(failed.group(1)) if failed else 0,
    }


def parse_total_coverage(output: str) -> int | None:
    match = TOTAL_COVERAGE.search(output)
    return int(match.group(1)) if match else None


def parse_mypy_files(output: str) -> int | None:
    match = MYPY_FILES.search(output)
    return int(match.group(1)) if match else None


def last_lines(output: str, count: int = 3) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return " | ".join(lines[-count:]) if lines else "no output"


def axis(name: str, status: str, evidence: str) -> dict[str, str]:
    return {"name": name, "status": status, "evidence": evidence}


def run_checks(root: Path, run: Runner) -> list[dict[str, str]]:
    axes: list[dict[str, str]] = []
    code, out = run(["uv", "run", "ruff", "check", "."], root)
    axes.append(axis("Lint", "PASS" if code == 0 else "FAIL", last_lines(out, 2)))
    code, out = run(["uv", "run", "mypy", "."], root)
    files = parse_mypy_files(out)
    detail = f"no issues in {files} source files" if code == 0 and files else last_lines(out, 3)
    axes.append(axis("Types", "PASS" if code == 0 else "FAIL", detail))
    code, out = run(["uv", "run", "pytest", "-q"], root)
    counts, total = parse_pytest(out), parse_total_coverage(out)
    detail = f"{counts['passed']} passed, {counts['failed']} failed"
    detail += f", coverage {total}%" if total is not None else ""
    axes.append(axis("Tests", "PASS" if code == 0 else "FAIL", detail))
    gate = [
        "uv",
        "run",
        "coverage",
        "report",
        "--include=reviews/services.py,reviews/repositories.py",
        "--fail-under=90",
    ]
    code, out = run(gate, root)
    gate_total = parse_total_coverage(out)
    detail = (
        f"{gate_total}% on services and repositories, gate 90%"
        if gate_total is not None
        else last_lines(out)
    )
    axes.append(axis("Coverage", "PASS" if code == 0 else "FAIL", detail))
    code, out = run(
        [
            "uv",
            "run",
            "pytest",
            ".claude/hooks/tests",
            ".claude/skills",
            "-q",
            "--no-cov",
            "-p",
            "no:cacheprovider",
        ],
        root,
    )
    detail = f"{parse_pytest(out)['passed']} passed, {parse_pytest(out)['failed']} failed"
    axes.append(axis("Skill and hook tests", "PASS" if code == 0 else "FAIL", detail))
    return axes


def issue_axis(data: dict[str, Any] | None) -> dict[str, str]:
    if not data or not data.get("criteria"):
        return axis("Issue", "NOT CONFIGURED", "no criteria were given (use --criteria)")
    criteria = data["criteria"]
    failed = [c for c in criteria if c.get("status") == "FAIL"]
    pending = [c for c in criteria if c.get("status") not in ("PASS", "FAIL")]
    status = "FAIL" if failed else "NOT CONFIGURED" if pending else "PASS"
    passed = len([c for c in criteria if c.get("status") == "PASS"])
    return axis("Issue", status, f"{passed} of {len(criteria)} criteria pass")


def query_axis(root: Path) -> dict[str, str]:
    files = (
        list((root / "reviews" / "tests").rglob("test_*.py")) if (root / "reviews").exists() else []
    )
    counts = [len(QUERY_ASSERTION.findall(f.read_text())) for f in files]
    total = sum(counts)
    if total == 0:
        return axis("Query count", "NOT CONFIGURED", "no test asserts a query count")
    holding = len([c for c in counts if c])
    return axis("Query count", "PASS", f"{total} query-count assertions in {holding} test files")


def secret_pattern() -> re.Pattern[str]:
    path = SKILLS.parent / "hooks" / "before-commit-check.py"
    spec = importlib.util.spec_from_file_location("commit_hook", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pattern: re.Pattern[str] = module.SECRET
    return pattern


def security_axis(diff: str) -> dict[str, str]:
    pattern = secret_pattern()
    hits = [
        line
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++") and pattern.search(line)
    ]
    if hits:
        return axis("Security", "FAIL", f"{len(hits)} added line(s) look like a secret (not shown)")
    return axis("Security", "PASS", "no secret-like string in the added lines of the diff")


def browser_axis(result_dir: Path | None, code: int | None, output: str) -> dict[str, str]:
    if result_dir is None or code is None:
        return axis("Browser", "NOT CONFIGURED", "not run (add --browser)")
    if code == 2:
        return axis("Browser", "NOT CONFIGURED", last_lines(output, 1))
    data = json.loads((result_dir / "result.json").read_text())
    shots = len(data["steps"])
    detail = (
        f"{len(data['steps'])} step(s), {shots} screenshot{'s' if shots != 1 else ''}, "
        f"console {data['console_errors']} error(s), network {data['network_failures']} failure(s)"
    )
    return axis("Browser", "PASS" if data["status"] == "clean" else "FAIL", detail)


def review_axis(text: str | None) -> dict[str, str] | None:
    if not text:
        return None
    first = text.strip().splitlines()[0]
    match = re.match(r"Status:\s*(PASS|FAIL|NOT CONFIGURED)", first)
    status = match.group(1) if match else "NOT CONFIGURED"
    return axis("Review", status, "see the review text below")


def verdict(axes: list[dict[str, str]]) -> str:
    states = {a["status"] for a in axes}
    if "FAIL" in states:
        return "FAIL"
    return "INCOMPLETE" if "NOT CONFIGURED" in states else "PASS"


CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#5a5a5a;--line:#d9d9d9;--pass:#176a2a;--fail:#a61b1b;
--warn:#8a5a00;--card:#f6f6f4}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#ececec;--muted:#a8a8a8;
--line:#3a3a3a;--pass:#58c46f;--fail:#ff7b7b;--warn:#e0b04a;--card:#1f1f1f}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0;padding:24px}
main{max-width:980px;margin:0 auto}h1{margin:.2em 0}h2{margin-top:1.6em}
.meta{color:var(--muted)}table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
.PASS{color:var(--pass);font-weight:700}.FAIL{color:var(--fail);font-weight:700}
.NOT\\ CONFIGURED,.INCOMPLETE{color:var(--warn);font-weight:700}
.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.shots figure{margin:0;background:var(--card);padding:8px;border-radius:8px}
.shots img{width:100%;height:auto;border:1px solid var(--line)}
pre{background:var(--card);padding:12px;overflow:auto;white-space:pre-wrap}
"""


def render_html(report: dict[str, Any]) -> str:
    esc = html.escape
    rows = "".join(
        f'<tr><td>{esc(a["name"])}</td><td class="{esc(a["status"])}">{esc(a["status"])}</td>'
        f"<td>{esc(a['evidence'])}</td></tr>"
        for a in report["axes"]
    )
    shots = ""
    for path in report.get("screenshots", []):
        data = base64.b64encode(Path(path).read_bytes()).decode()
        shots += (
            f'<figure><img alt="{esc(Path(path).stem)}" src="data:image/png;base64,{data}">'
            f"<figcaption>{esc(Path(path).stem)}</figcaption></figure>"
        )
    check = "".join(f"<li>{esc(item)}</li>" for item in report.get("check_yourself", []))
    review = f"<h2>Review</h2><pre>{esc(report['review'])}</pre>" if report.get("review") else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Verify report</title><style>{CSS}</style></head><body><main>"
        f"<h1>Verify report: {esc(report['title'])}</h1>"
        f'<p class="meta">Branch {esc(report["branch"])} · commit {esc(report["commit"])} · '
        f"{esc(report['date'])}</p>"
        f'<h2>Result: <span class="{esc(report["verdict"])}">{esc(report["verdict"])}</span></h2>'
        f"<table><thead><tr><th>Axis</th><th>Result</th><th>Evidence</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        + (f'<h2>Screenshots</h2><div class="shots">{shots}</div>' if shots else "")
        + review
        + (f"<h2>What to check yourself</h2><ol>{check}</ol>" if check else "")
        + "</main></body></html>"
    )


def git_value(root: Path, run: Runner, *args: str) -> str:
    code, out = run(["git", *args], root)
    return out.strip() if code == 0 and out.strip() else "unknown"


def build(
    root: Path,
    out_dir: Path,
    run: Runner,
    title: str,
    criteria: dict[str, Any] | None,
    review: str | None,
    browser: bool,
    open_report: bool,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    axes = run_checks(root, run)
    axes.append(issue_axis(criteria))
    axes.append(query_axis(root))
    _, diff = run(["git", "diff", "HEAD", "-U0"], root)
    axes.append(security_axis(diff))
    shots: list[str] = []
    if browser:
        script = SKILLS / "check-in-browser" / "browser_check.py"
        folder = out_dir / "browser"
        code, text = run([sys.executable, str(script), "--out", str(folder)], root)
        axes.append(
            browser_axis(folder if (folder / "result.json").is_file() else None, code, text)
        )
        if (folder / "result.json").is_file():
            steps = json.loads((folder / "result.json").read_text())["steps"]
            shots = [str(folder / s["screenshot"]) for s in steps]
    else:
        axes.append(browser_axis(None, None, ""))
    extra = review_axis(review)
    if extra:
        axes.append(extra)
    report: dict[str, Any] = {
        "title": title,
        "verdict": verdict(axes),
        "branch": git_value(root, run, "branch", "--show-current"),
        "commit": git_value(root, run, "rev-parse", "--short", "HEAD"),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "axes": axes,
        "screenshots": shots,
        "review": review or "",
        "check_yourself": (criteria or {}).get("check_yourself", []),
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    page = out_dir / "report.html"
    page.write_text(render_html(report))
    if open_report:
        webbrowser.open(page.as_uri())
    return report


def project_root(start: Path) -> Path:
    for folder in (start, *start.parents):
        if (folder / "manage.py").is_file():
            return folder
    return start


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build the verify report.")
    parser.add_argument("--title", required=True, help="the issue, as a short title")
    parser.add_argument("--criteria", type=Path, help="JSON: criteria with status, check_yourself")
    parser.add_argument("--review", type=Path, help="text file; first line Status: PASS or FAIL")
    parser.add_argument("--browser", action="store_true", help="run the browser check too")
    parser.add_argument("--no-open", action="store_true", help="do not open the report")
    parser.add_argument("--out", type=Path, help="folder (default: out/verify/<time>)")
    args = parser.parse_args(argv)
    root = project_root(Path.cwd())
    out_dir = args.out or root / "out" / "verify" / datetime.now().strftime("%Y%m%d-%H%M%S")
    criteria = json.loads(args.criteria.read_text()) if args.criteria else None
    review = args.review.read_text() if args.review else None
    report = build(
        root, out_dir, real_run, args.title, criteria, review, args.browser, not args.no_open
    )
    for item in report["axes"]:
        print(f"{item['status']:<15} {item['name']:<22} {item['evidence']}")
    print(f"result: {report['verdict']}   report: {out_dir / 'report.html'}")
    return {"PASS": 0, "FAIL": 1}.get(report["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
