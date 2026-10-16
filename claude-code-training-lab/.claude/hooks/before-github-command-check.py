#!/usr/bin/env python3
"""Before every Bash call: refuse gh, git and curl commands that reach a GitHub repository
other than the allowed one, or that manage repositories, accounts or secrets.

The call arrives as JSON on stdin. Exit code 2 blocks it and sends stderr back to Claude.
The allowed repository is the first line of github-allowed-repo.txt (owner/name).
If anything goes wrong while checking a command that looks relevant, the command is blocked.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
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
    if RELEVANT.search(command) is None:
        return []
    problems: list[str] = []
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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    if RELEVANT.search(command) is None:
        return 0
    try:
        problems = check_command(command, read_allowed())
        allowed_name = read_allowed()
    except Exception as error:  # fail closed for anything that looks relevant
        problems = [f"the guard could not check this command ({error})"]
        allowed_name = "the allowed repository"
    if not problems:
        return 0
    print(
        f"Blocked by before-github-command-check: {'; '.join(problems)}. "
        f"Only {allowed_name} may be reached from here (see .claude/rules/security.md).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
