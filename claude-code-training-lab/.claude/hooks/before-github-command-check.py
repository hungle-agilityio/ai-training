#!/usr/bin/env python3
"""Before every Bash call: refuse gh, git and curl commands that reach a GitHub repository
other than the allowed one, or that manage repositories, accounts or secrets.

The call arrives as JSON on stdin. Exit code 2 blocks it and sends stderr back to Claude.
The allowed repository is the first line of github-allowed-repo.txt (owner/name).
If anything goes wrong while checking a command that looks relevant, the command is blocked.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ALLOWED_FILE = Path(__file__).with_name("github-allowed-repo.txt")

GH_TOP_LEVEL = {
    "issue", "pr", "label", "run", "workflow", "release", "repo", "api", "auth", "version", "help",
}
GIT_NETWORK = {"push", "pull", "fetch", "ls-remote"}

ADMIN_GH = re.compile(
    r"\bgh\s+(?:repo\s+(?:create|delete|edit|rename|archive|unarchive|fork|transfer|clone|sync"
    r"|list|deploy-key)"
    r"|auth\s+(?:login|logout|refresh|token|switch|setup-git)"
    r"|gist|ssh-key|gpg-key|org|secret|variable|codespace|extension|alias|search)\b"
)
RELEVANT = re.compile(
    r"\bgh\b|\bgit\b|github|\bcurl\b|\bwget\b|\bssh\b|\bscp\b|\bsftp\b|\brsync\b"
)
QUOTED_HEREDOC = re.compile(r"<<-?\s*'(\w+)'[^\n]*\n.*?\n\s*\1[ \t]*(?:\n|$)", re.S)
SHELL_WORD = re.compile(r"\b(?:bash|sh|zsh|dash|ksh|eval|source)\b")
CONFIG_READ_FLAGS = {"--get", "--get-all", "--get-regexp", "--get-urlmatch", "--list", "-l"}
REMOTE_KEY = re.compile(r"\bremote\.[^\s]+\.(?:url|pushurl)\b|\burl\.")
TOKEN_USE = re.compile(
    r"\b(?:GH_TOKEN|GITHUB_TOKEN|GITHUB_PERSONAL_ACCESS_TOKEN)\b"
    r"|(?:^|[;&|\n]\s*)(?:printenv|env)\s*(?:$|[;&|\n])"
)
SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
ENV_PREFIX = r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
GH_SEGMENT = re.compile(rf"^{ENV_PREFIX}(?:sudo\s+)?gh\b\s*(.*)$", re.S)
GIT_SEGMENT = re.compile(rf"^{ENV_PREFIX}git\b\s*(.*)$", re.S)
FETCH_SEGMENT = re.compile(rf"^{ENV_PREFIX}(?:curl|wget)\b")
SSH_SEGMENT = re.compile(rf"^{ENV_PREFIX}(?:ssh|scp|sftp|rsync)\b")
REPO_IN_URL = re.compile(r"(?<![\w.-])github\.com[/:]+([\w.-]+)/([\w.-]+)")
REPO_IN_API = re.compile(r"(?:^|[\s'\"/])repos/([\w.-]+)/([\w.-]+)")
API_HOST_PATH = re.compile(r"api\.github\.com(/[^\s'\"]*)")
GH_REPO_ENV = re.compile(r"\bGH_REPO=['\"]?([^\s'\"]+)")


def normalise(owner: str, name: str) -> str:
    """Return owner/name in lower case without a .git suffix."""
    if name.endswith(".git"):
        name = name[:-4]
    return f"{owner}/{name}".lower()


def repo_from_value(value: str) -> str:
    """Turn a -R value (owner/name, host/owner/name or a URL) into owner/name."""
    parts = [part for part in value.strip("/").split("/") if part]
    if len(parts) >= 2:
        return normalise(parts[-2], parts[-1])
    return value.lower()


def url_like(token: str) -> bool:
    return "://" in token or re.match(r"^[\w.-]+@[\w.-]+:", token) is not None


def repo_of_url(token: str) -> str | None:
    match = REPO_IN_URL.search(token)
    return normalise(match.group(1), match.group(2)) if match else None


def foreign_in_text(text: str, allowed: str) -> list[str]:
    """Repositories named by URL or API path in text that are not the allowed one."""
    found = [normalise(o, n) for o, n in REPO_IN_URL.findall(text) + REPO_IN_API.findall(text)]
    return [f"it reaches {name}" for name in found if name != allowed]


def foreign_urls(urls: list[str], allowed: str) -> list[str]:
    return [f"it reaches {repo_of_url(u) or u}" for u in urls if repo_of_url(u) != allowed]


def check_gh(rest: str, allowed: str) -> list[str]:
    try:
        tokens = shlex.split(rest)
    except ValueError:
        return ["the gh command could not be read safely"]
    problems: list[str] = []
    for index, token in enumerate(tokens):
        value = ""
        if token in ("-R", "--repo") and index + 1 < len(tokens):
            value = tokens[index + 1]
        elif token.startswith("--repo="):
            value = token.split("=", 1)[1]
        if value and repo_from_value(value) != allowed:
            problems.append(f"it targets {repo_from_value(value)}")
    positional = [token for token in tokens if not token.startswith("-")]
    if not positional:
        return problems
    top = positional[0]
    if top not in GH_TOP_LEVEL:
        problems.append(f"gh {top} is not allowed here")
    elif top == "auth" and (len(positional) < 2 or positional[1] != "status"):
        problems.append("only gh auth status is allowed")
    elif top == "repo":
        if len(positional) < 2 or positional[1] != "view":
            problems.append("only gh repo view is allowed")
        elif len(positional) > 2 and repo_from_value(positional[2]) != allowed:
            problems.append(f"it targets {repo_from_value(positional[2])}")
    elif top == "api":
        problems.extend(check_api(tokens, positional, allowed))
    problems.extend(foreign_in_text(rest, allowed))
    return problems


def check_api(tokens: list[str], positional: list[str], allowed: str) -> list[str]:
    problems: list[str] = []
    for index, token in enumerate(tokens):
        method = ""
        if token in ("-X", "--method") and index + 1 < len(tokens):
            method = tokens[index + 1]
        elif token.startswith("--method="):
            method = token.split("=", 1)[1]
        if method.upper() == "DELETE":
            problems.append("gh api with DELETE is not allowed")
    if len(positional) < 2:
        return problems
    path = positional[1].lstrip("/").lower()
    if not (path.startswith(f"repos/{allowed}") or path in ("user", "rate_limit")):
        problems.append(f"gh api path {positional[1]} is outside {allowed}")
    return problems


def check_git(rest: str, allowed: str) -> list[str]:
    try:
        tokens = shlex.split(rest)
    except ValueError:
        if re.search(r"\b(push|pull|fetch|clone|ls-remote|remote)\b", rest):
            return ["the git command could not be read safely"]
        return []
    index = 0
    while index < len(tokens) and tokens[index].startswith("-"):
        index += 2 if tokens[index] in ("-C", "-c", "--git-dir", "--work-tree") else 1
    if index >= len(tokens):
        return []
    sub, args = tokens[index], tokens[index + 1:]
    positional = [arg for arg in args if not arg.startswith("-")]
    problems: list[str] = []
    if sub == "config":
        reading = any(arg in CONFIG_READ_FLAGS for arg in args)
        if not reading and (REMOTE_KEY.search(rest.lower()) or "insteadof" in rest.lower()):
            problems.append("changing remote URLs with git config is not allowed")
    elif sub in GIT_NETWORK:
        if positional:
            first = positional[0]
            target = repo_of_url(first) if url_like(first) else first
            if target not in ("origin", allowed):
                problems.append(f"git {sub} must use origin or {allowed}, not {first}")
    elif sub == "clone":
        urls = [arg for arg in positional if url_like(arg)]
        problems.extend(foreign_urls(urls, allowed))
    elif sub == "remote" and positional and positional[0] in ("add", "set-url"):
        urls = [arg for arg in positional[1:] if url_like(arg)]
        if not urls:
            problems.append(f"the remote URL must be a github.com URL of {allowed}")
        problems.extend(foreign_urls(urls, allowed))
    return problems


def check_ssh(text: str) -> list[str]:
    """Direct ssh, scp, sftp or rsync to github.com is only allowed as the ssh -T test."""
    if "github" not in text.lower():
        return []
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = []
    if tokens and tokens[0] == "ssh" and "-T" in tokens and tokens[-1].lower() == "git@github.com":
        return []
    return ["direct ssh to github.com is only allowed as the ssh -T connection test"]


def without_inert_heredocs(command: str) -> str:
    """Drop heredoc bodies with a quoted delimiter, unless a shell would run them."""

    def drop(match: re.Match[str]) -> str:
        line_start = command.rfind("\n", 0, match.start()) + 1
        head = command[line_start:match.start()] + match.group(0).split("\n", 1)[0]
        return match.group(0) if SHELL_WORD.search(head) else "\n"

    return QUOTED_HEREDOC.sub(drop, command)


def check_fetch_tool(segment: str, allowed: str) -> list[str]:
    problems = foreign_in_text(segment, allowed)
    for path in API_HOST_PATH.findall(segment):
        clean = path.split("?")[0].lstrip("/").lower()
        if not (clean.startswith(f"repos/{allowed}") or clean in ("user", "rate_limit")):
            problems.append(f"api.github.com path {path} is outside {allowed}")
    return problems


def check_command(command: str, allowed: str) -> list[str]:
    """Return the reasons to block a command, or an empty list when it may run."""
    command = without_inert_heredocs(command)
    problems: list[str] = []
    if TOKEN_USE.search(command):
        problems.append("the token must never be read or printed (GH_TOKEN, printenv, env)")
    if RELEVANT.search(command) is None:
        return problems
    if ADMIN_GH.search(command):
        problems.append("gh commands that manage repositories, accounts or secrets are not allowed")
    for segment in SEGMENT_SPLIT.split(command):
        text = segment.strip()
        for env_value in GH_REPO_ENV.findall(text):
            if repo_from_value(env_value) != allowed:
                problems.append(f"GH_REPO points to {repo_from_value(env_value)}")
        if match := GH_SEGMENT.match(text):
            problems.extend(check_gh(match.group(1), allowed))
        elif match := GIT_SEGMENT.match(text):
            problems.extend(check_git(match.group(1), allowed))
        elif FETCH_SEGMENT.match(text):
            problems.extend(check_fetch_tool(text, allowed))
        elif SSH_SEGMENT.match(text):
            problems.extend(check_ssh(text))
    return list(dict.fromkeys(problems))


def read_allowed() -> str:
    for line in ALLOWED_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line.lower()
    raise ValueError("github-allowed-repo.txt has no repository")


LOOP_ENV = "REVIEWRADAR_LOOP"
LOOP_BRANCH = re.compile(r"^(?:bug|feat|task)/\d+-[a-z0-9][a-z0-9-]*$")
FORCE_FLAGS = {"--mirror", "--delete", "--prune", "--all"}
MAIN_NAMES = {"main", "master"}
MERGE_FLAGS = {"--merge", "-m"}
SHA = re.compile(r"^[0-9a-f]{7,40}$")
API_MERGE = re.compile(r"(?:^|/)(?:pulls/\d+/merge|merges|git/refs)(?:/|$|\?)", re.I)
API_WRITE = {"POST", "PUT", "PATCH"}
MERGE_USAGE = "gh pr merge must be exactly: gh pr merge <number> --merge --match-head-commit <sha>"
GitRunner = Callable[[list[str]], tuple[int, str]]


def push_problems(args: list[str], run: GitRunner) -> list[str]:
    """A push may never force, delete, push everything or reach main, in any mode."""
    flags = [arg for arg in args if arg.startswith("-")]
    positional = [arg for arg in args if not arg.startswith("-")]
    problems: list[str] = []
    for flag in flags:
        short = set(flag[1:]) if not flag.startswith("--") else set()
        if flag in FORCE_FLAGS or flag.startswith("--force") or short & {"f", "d"}:
            problems.append(f"git push {flag} is not allowed (force, delete or everything)")
    refspecs = positional[1:]
    for spec in refspecs:
        target = spec.split(":", 1)[-1].removeprefix("refs/heads/")
        if spec.startswith(("+", ":")) or target in MAIN_NAMES:
            problems.append(f"git push {spec} is not allowed (force, delete or main)")
    if not refspecs or any(spec in ("HEAD", "@") for spec in refspecs):
        code, branch = run(["git", "branch", "--show-current"])
        if code != 0 or branch.strip() in MAIN_NAMES or not branch.strip():
            problems.append("git push needs a current branch that is not main")
    return problems


def merge_problems(args: list[str], run: GitRunner) -> tuple[list[str], str]:
    """A merge is exact, names the head commit the user saw, and is never the loop's own."""
    number = sha = ""
    merge = False
    index = 0
    while index < len(args):
        token = args[index]
        if token in MERGE_FLAGS:
            merge = True
        elif token == "--match-head-commit" and index + 1 < len(args):
            sha = args[index + 1].lower()
            index += 1
        elif token.startswith("--match-head-commit="):
            sha = token.split("=", 1)[1].lower()
        elif not token.startswith("-") and not number and token.isdigit():
            number = token
        else:
            return [MERGE_USAGE], ""
        index += 1
    if not (merge and number and SHA.match(sha)):
        return [MERGE_USAGE], ""
    fields = "state,headRefName,headRefOid,baseRefName,isCrossRepository"
    code, out = run(["gh", "pr", "view", number, "--json", fields])
    try:
        data = json.loads(out) if code == 0 else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return ["the pull request could not be read, so the merge cannot be checked"], ""
    problems: list[str] = []
    if data.get("state") != "OPEN":
        problems.append("the pull request is not open")
    if not LOOP_BRANCH.match(str(data.get("headRefName", ""))):
        problems.append("only an issue branch (kind/number-description) may be merged here")
    if data.get("baseRefName") != "main" or data.get("isCrossRepository"):
        problems.append("only a same-repository pull request into main may be merged here")
    if not str(data.get("headRefOid", "")).lower().startswith(sha):
        problems.append("--match-head-commit is not the pull request's current head commit")
    summary = f"gh pr merge {number} ({data.get('headRefName')}, head {sha[:7]})"
    return problems, summary


def api_problems(tokens: list[str], positional: list[str]) -> list[str]:
    """gh api must not be a side door to merge or move a ref."""
    if len(positional) < 2:
        return []
    method = "GET"
    path = next((token for token in tokens if API_MERGE.search(token)), "")
    for index, token in enumerate(tokens):
        if token in ("-X", "--method") and index + 1 < len(tokens):
            method = tokens[index + 1].upper()
        elif token.startswith("--method="):
            method = token.split("=", 1)[1].upper()
        elif token in ("-f", "-F", "--field", "--raw-field", "--input") and method == "GET":
            method = "POST"
    if method in API_WRITE and path:
        return [f"gh api {method} {path} would merge or move a ref; use gh pr merge"]
    return []


def check_publish(command: str, loop: bool, run: GitRunner) -> tuple[str, list[str]]:
    """Decide push, pull request and merge: ('allow' | 'ask' | 'deny', reasons)."""
    problems: list[str] = []
    ask: list[str] = []
    segments = [s.strip() for s in SEGMENT_SPLIT.split(without_inert_heredocs(command))]
    segments = [segment for segment in segments if segment]
    moves = any(re.match(r"^(?:cd|pushd)\b", segment) for segment in segments)
    for segment in segments:
        gh = GH_SEGMENT.match(segment)
        git = None if gh else GIT_SEGMENT.match(segment)
        if not gh and not git:
            continue
        rest = (gh or git).group(1)  # type: ignore[union-attr]
        try:
            tokens = shlex.split(rest)
        except ValueError:
            if re.search(r"\b(push|merge|create|api)\b", rest):
                problems.append("the command could not be read safely")
            continue
        if git:
            index = 0
            while index < len(tokens) and tokens[index].startswith("-"):
                index += 2 if tokens[index] in ("-C", "-c", "--git-dir", "--work-tree") else 1
            if index < len(tokens) and tokens[index] == "push":
                if index > 0 or moves:
                    problems.append("git push must run in the current folder, without options")
                problems.extend(push_problems(tokens[index + 1 :], run))
                if not loop:
                    ask.append("git push needs your approval outside loop mode")
            continue
        positional = [token for token in tokens if not token.startswith("-")]
        if positional[:1] == ["api"]:
            problems.extend(api_problems(tokens, positional))
        elif positional[:2] == ["pr", "create"] and not loop:
            ask.append("opening a pull request needs your approval outside loop mode")
        elif positional[:2] == ["pr", "merge"]:
            if loop:
                problems.append("the loop never merges; the owner merges in an interactive session")
            elif len(segments) > 1:
                problems.append("gh pr merge must be the only command in the call")
            else:
                found, summary = merge_problems(tokens[tokens.index("merge") + 1 :], run)
                problems.extend(found)
                ask.append(f"merge: {summary}")
    if problems:
        return "deny", list(dict.fromkeys(problems))
    return ("ask", ask) if ask else ("allow", [])


def publish_gate(command: str, cwd: str) -> int:
    def run(args: list[str]) -> tuple[int, str]:
        try:
            done = subprocess.run(
                args, cwd=cwd, capture_output=True, text=True, timeout=30, check=False
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return 127, ""
        return done.returncode, done.stdout

    loop = os.environ.get(LOOP_ENV) == "1"
    try:
        decision, reasons = check_publish(command, loop, run)
    except Exception as error:  # fail closed
        decision, reasons = "deny", [f"the publish guard failed ({error})"]
    if decision == "deny":
        message = "; ".join(reasons)
        print(f"Blocked by before-github-command-check: {message}.", file=sys.stderr)
        return 2
    if decision == "ask":
        reply = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "; ".join(reasons),
            }
        }
        print(json.dumps(reply))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    plain = without_inert_heredocs(command)
    if RELEVANT.search(command) is None and TOKEN_USE.search(plain) is None:
        return 0
    try:
        problems = check_command(command, read_allowed())
        allowed_name = read_allowed()
    except Exception as error:  # fail closed for anything that looks relevant
        problems = [f"the guard could not check this command ({error})"]
        allowed_name = "the allowed repository"
    if not problems:
        return publish_gate(command, str(payload.get("cwd") or os.getcwd()))
    print(
        f"Blocked by before-github-command-check: {'; '.join(problems)}. "
        f"Only {allowed_name} may be reached from here (see .claude/rules/security.md).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
