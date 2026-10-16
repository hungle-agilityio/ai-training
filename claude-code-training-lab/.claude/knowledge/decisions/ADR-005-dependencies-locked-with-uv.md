# ADR-005: Dependencies are locked with uv

- Status: Accepted
- Date: 2026-10-16

## Context

`requirements.txt` held only version ranges, `pyproject.toml` declared no dependency, and `uv.lock` was an empty ignored stub. On a fresh clone `uv run pytest` failed with "Failed to spawn: pytest".

## Decision

Dependencies are declared in `pyproject.toml` (the app, and a `dev` group for the tools) and locked in `uv.lock`, which is committed. Install with `uv sync`; the automatic checks use `uv sync --frozen`.

## Consequences

`requirements.txt` is removed. Two fresh installs give identical versions. Upgrades are a deliberate `uv lock --upgrade` reviewed in a pull request.
