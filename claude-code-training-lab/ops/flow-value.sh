#!/usr/bin/env bash
# Sourced by start-loop.sh and install-launchd.sh: `flow_value loop.tmux_session` prints one value
# of ops/flow.toml (or the file named by FLOW_CONFIG). Spec: specs/flow-bootstrap/spec.md (AC5).
# It asks `python3 ops/flow_config.py` (the checked reader, Python 3.11+). The macOS system
# python3 is older and has no tomllib, so for a plain `key = "value"` line it reads the file itself.

flow_value() {
  local dir file key value err
  dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  file="${FLOW_CONFIG:-$dir/flow.toml}"
  key="${1#*.}"
  if python3 -c 'import tomllib' 2>/dev/null; then
    python3 "$dir/flow_config.py" "$1"
    return $?
  fi
  value="$(sed -n "s/^$key[[:space:]]*=[[:space:]]*\"\\(.*\\)\"[[:space:]]*\$/\\1/p" "$file" 2>/dev/null | head -n 1)"
  if [ -z "$value" ]; then
    err="$(python3 "$dir/flow_config.py" "$1" 2>&1 || true)"
    echo "flow.toml: cannot read $1 (${err:-no value in $file})" >&2
    return 2
  fi
  printf '%s\n' "${value/#\~/$HOME}"
}
