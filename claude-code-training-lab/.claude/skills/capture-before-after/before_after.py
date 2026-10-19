#!/usr/bin/env python3
"""Capture the same steps before and after a change, on the same demo data, and pair them.

Usage: uv run python .claude/skills/capture-before-after/before_after.py [--base REF]
       [--spec FILE] [--out DIR]

The base (the "before") is checked out in a temporary git worktree, so the working folder is not
touched. Both sides run the same steps in the same window size, each on a throw-away demo
database. Pairs are matched by step name and labelled: changed, no visible difference, did not
exist before, or not captured. Writes compare.html and compare.json next to the screenshots.

Exit code: 0 done and masking clean, 2 could not run, 3 personal data was found (masking).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

Runner = Callable[[list[str], Path], tuple[int, str]]
SKILLS = Path(__file__).resolve().parents[1]


def real_run(args: list[str], cwd: Path) -> tuple[int, str]:
    done = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    return done.returncode, done.stdout + done.stderr


def load_skill(folder: str, file: str) -> Any:
    spec = importlib.util.spec_from_file_location(file, SKILLS / folder / f"{file}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_base(root: Path, requested: str | None, run: Runner = real_run) -> str:
    """The ref to compare with: the one given, else the merge base with main."""
    if requested:
        return requested
    code, _ = run(["git", "show", "main:./manage.py"], root)
    if code != 0:
        raise ValueError("main does not hold the project yet: give the base with --base <ref>")
    code, out = run(["git", "merge-base", "main", "HEAD"], root)
    if code != 0 or not out.strip():
        raise ValueError("no merge base with main: give the base with --base <ref>")
    return out.strip()


def project_in(tree: Path, prefix: str) -> Path:
    folder = prefix.strip().strip("/")
    return tree / folder if folder else tree


@contextmanager
def checkout(root: Path, ref: str, run: Runner = real_run) -> Iterator[Path]:
    """A temporary worktree of ref, removed afterwards."""
    folder = Path(tempfile.mkdtemp(prefix="before-after-"))
    tree = folder / "tree"
    code, out = run(["git", "worktree", "add", "--detach", str(tree), ref], root)
    if code != 0:
        shutil.rmtree(folder, ignore_errors=True)
        raise ValueError(
            f"could not check out {ref}: {out.strip().splitlines()[-1] if out else ''}"
        )
    try:
        yield tree
    finally:
        run(["git", "worktree", "remove", "--force", str(tree)], root)
        shutil.rmtree(folder, ignore_errors=True)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_steps(
    before: list[dict[str, Any]], before_dir: Path, after: list[dict[str, Any]], after_dir: Path
) -> list[dict[str, Any]]:
    """Match the steps by name and label each pair."""
    names = [s["name"] for s in before] + [
        s["name"] for s in after if s["name"] not in {b["name"] for b in before}
    ]
    by_before = {s["name"]: s for s in before}
    by_after = {s["name"]: s for s in after}
    pairs: list[dict[str, Any]] = []
    for name in names:
        old, new = by_before.get(name), by_after.get(name)
        if old is None:
            label = "not captured before"
        elif new is None:
            label = "not captured after"
        elif old.get("http_status") == 404 and new.get("http_status") != 404:
            label = "did not exist before"
        elif digest(before_dir / old["screenshot"]) == digest(after_dir / new["screenshot"]):
            label = "no visible difference"
        else:
            label = "changed"
        pairs.append(
            {
                "name": name,
                "label": label,
                "before": str(before_dir / old["screenshot"]) if old else None,
                "after": str(after_dir / new["screenshot"]) if new else None,
                "url": (new or old or {}).get("url", ""),
            }
        )
    return pairs


def image(path: str | None) -> str:
    if not path:
        return "<p>not captured</p>"
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f'<img alt="{html.escape(Path(path).stem)}" src="data:image/png;base64,{data}">'


def render_compare_html(title: str, base: str, head: str, pairs: list[dict[str, Any]]) -> str:
    css = load_skill("build-verify-report", "build_report").CSS
    esc = html.escape
    rows = "".join(
        f'<h2>{esc(p["name"])} <span class="meta">{esc(p["url"])}</span></h2>'
        f"<p><strong>{esc(p['label'])}</strong></p>"
        '<div class="pair"><figure>'
        f"<figcaption>Before ({esc(base)})</figcaption>{image(p['before'])}</figure>"
        f"<figure><figcaption>After ({esc(head)})</figcaption>{image(p['after'])}</figure></div>"
        for p in pairs
    )
    extra = ".pair{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}"
    extra += ".pair figure{margin:0}.pair img{width:100%;height:auto;border:1px solid var(--line)}"
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Before and after</title><style>{css}{extra}</style></head><body><main>"
        f"<h1>Before and after: {esc(title)}</h1>{rows}</main></body></html>"
    )


def capture(root: Path, steps: list[dict[str, Any]], folder: Path) -> dict[str, Any]:
    browser = load_skill("check-in-browser", "browser_check")
    summary: dict[str, Any] = browser.run(root, steps, folder)
    return summary


def combined_masking(*summaries: dict[str, Any]) -> dict[str, Any]:
    """clean only when every side is clean; findings are listed with their side."""
    findings = [f for summary in summaries for f in summary["masking"].get("findings", [])]
    clean = all(summary["masking"]["status"] == "clean" for summary in summaries)
    return {"status": "clean" if clean else "findings", "findings": findings}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Capture the same steps before and after a change."
    )
    parser.add_argument("--base", help="the ref to compare with (default: merge base with main)")
    parser.add_argument("--spec", type=Path, help="JSON steps (default: the reviews pages)")
    parser.add_argument("--out", type=Path, help="folder (default: out/before-after/<time>)")
    args = parser.parse_args(argv)
    browser = load_skill("check-in-browser", "browser_check")
    root = browser.project_root(Path.cwd())
    out = args.out or root / "out" / "before-after" / datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        base = resolve_base(root, args.base)
        steps = browser.load_steps(args.spec)
        code, prefix = real_run(["git", "rev-parse", "--show-prefix"], root)
        with checkout(root, base) as tree:
            before_run = capture(
                project_in(tree, prefix if code == 0 else ""), steps, out / "before"
            )
        after_run = capture(root, steps, out / "after")
        before, after = before_run["steps"], after_run["steps"]
    except Exception as error:
        print(f"NOT RUN: {str(error).splitlines()[0] if str(error) else type(error).__name__}")
        return 2
    pairs = pair_steps(before, out / "before", after, out / "after")
    head = real_run(["git", "rev-parse", "--short", "HEAD"], root)[1].strip() or "HEAD"
    (out / "compare.html").write_text(render_compare_html(root.name, base[:12], head, pairs))
    masking = combined_masking(before_run, after_run)
    report = {"base": base, "head": head, "pairs": pairs, "masking": masking}
    (out / "compare.json").write_text(json.dumps(report, indent=2))
    for p in pairs:
        print(f"{p['label']:<24} {p['name']:<14} {p['url']}")
    print(f"masking: {masking['status']}")
    print(f"folder: {out}")
    return 0 if masking["status"] == "clean" else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
