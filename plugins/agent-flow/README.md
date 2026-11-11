# agent-flow

The issue-to-pull-request flow as a Claude Code plugin: the guard hooks, the flow skills, the slash commands and the sub-agents of a loop that builds labelled issues. It is listed by the marketplace `ai-training` at the root of this repository (`.claude-plugin/marketplace.json`).

It holds the guard hooks (`hooks/`, see `hooks/README.md`). The skills, commands and sub-agents move in with #223 (spec: `claude-code-training-lab/specs/flow-plugin/spec.md`).

A project turns the plugin on in its `.claude/settings.json` (`extraKnownMarketplaces` and `enabledPlugins`), and the hooks read that project's flow config through `$CLAUDE_PROJECT_DIR`: `.flow/flow.toml` when it exists (the new layout), else `ops/flow.toml`, or the file named by `FLOW_CONFIG`. The installed plugin only changes when its version does, so every change here raises the version in `.claude-plugin/plugin.json`.

## Project layout

The skills, commands and sub-agents name a project's folders by the keys of the optional `[paths]` table of its flow config, never by a fixed path. A missing key takes the default below, which is the layout of the project this plugin grew in; a project made by bootstrap writes the new layout.

| Key | What it holds | Default | New layout |
|---|---|---|---|
| `loop_dir` | the loop scripts and `flow_config.py` | `ops` | `.flow/loop` |
| `plugin_dir` | this plugin | `../plugins/agent-flow` | `.flow/plugin` |
| `intent_file` | the intent of one feature | `specs/{feature}/intent.md` | `docs/intent/{feature}.md` |
| `specs_dir` | the specs, one folder per feature | `specs` | `docs/specs` |
| `spec_pr_dirs` | the only folders a spec pull request changes | `specs`, `design` | `docs/intent`, `docs/specs` |
| `plans_dir` | approved plans (empty: not saved) | empty | `docs/plans` |
| `decisions_dir` | the decision records (ADRs) | `.claude/knowledge/decisions` | `docs/decisions` |
| `templates_dir` | the issue and spec templates | `docs/app/templates` | `docs/templates` |
| `code_dirs` | the product's code | the app folders | `src` |
| `flow_dirs` | the flow's own folders (`area:flow`) | `ops/`, `.claude/`, `.github/`, `specs/`, `docs/learning/` | `.flow/`, `.claude/`, `.github/`, `docs/intent/`, `docs/specs/`, `scripts/` |

The spec rule: a spec pull request changes only the folders of `paths.spec_pr_dirs`.

## Install

```
claude plugin marketplace add hungle-agilityio/ai-training
claude plugin install agent-flow@ai-training
```

Check it with `claude plugin validate plugins/agent-flow` (the plugin) and `claude plugin validate .` (the marketplace), both at the git root.

## Probe

Run by hand on the Mac mini on 2026-11-05 with Claude Code 2.1.318, to settle how the plugin behaves in the loop before the hooks and skills move in. A probe hook and a probe skill were added for the probe and removed again before the pull request:

- the hook ran on `SessionStart` and on `PreToolUse` for `Bash`, each time writing one JSON line with `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PROJECT_DIR`, `REVIEWRADAR_LOOP` and the payload `cwd`;
- the skill `flow-probe` had a script `probe.py`, which printed its own path, and a second script `other.py`.

### 1. Install route

A marketplace added from a local folder (`claude plugin marketplace add <git root>`) installs, but the plugin then runs from that folder: `CLAUDE_PLUGIN_ROOT` was the working tree's `plugins/agent-flow`, not the cache. To measure the real route, the marketplace was added from GitHub at the task branch:

```
$ claude plugin marketplace add "hungle-agilityio/ai-training#task/221-plugin-skeleton-marketplace"
✔ Successfully added marketplace: ai-training (declared in user settings)
$ claude plugin install agent-flow@ai-training
✔ Successfully installed plugin: agent-flow@ai-training (scope: user)
```

ReviewRadar's `settings.json` will name the GitHub source (#222), so this is the route the loop uses.

### 2. Hooks and skills fire in both kinds of session

In `claude -p`, started the way the tick starts builds (`env -u CLAUDE_CONFIG_DIR FLOW_LOOP=1 REVIEWRADAR_LOOP=1 claude -p "<prompt>" --allowedTools Artifact <rule>`, in `claude-code-training-lab/`), the prompt "Use the agent-flow:flow-probe skill" gave:

```
RAN:probe-skill-ran /Users/hungle/.claude/plugins/cache/ai-training/agent-flow/0.1.0/skills/flow-probe/probe.py
```

The hook log of that run, with the project paths shortened:

```
{"event": "SessionStart", "plugin_root": "/Users/hungle/.claude/plugins/cache/ai-training/agent-flow/0.1.0", "project_dir": ".../claude-code-training-lab", "loop": "1", "cwd": ".../claude-code-training-lab", "command": null}
{"event": "PreToolUse", "plugin_root": "/Users/hungle/.claude/plugins/cache/ai-training/agent-flow/0.1.0", "project_dir": ".../claude-code-training-lab", "loop": "1", "cwd": ".../claude-code-training-lab", "command": "python3 /Users/hungle/.claude/plugins/cache/ai-training/agent-flow/0.1.0/skills/flow-probe/probe.py"}
```

The interactive session (`claude --model haiku '<same prompt>'` in tmux, auto mode) gave:

```
⏺ Skill(agent-flow:flow-probe)
  ⎿  Successfully loaded skill
⏺ The probe script printed:
  probe-skill-ran /Users/hungle/.claude/plugins/cache/ai-training/agent-flow/0.1.1/skills/flow-probe/probe.py
```

It logged the same two hook lines. So:

- plugin hooks run in both kinds of session, and `REVIEWRADAR_LOOP` reaches them;
- `CLAUDE_PROJECT_DIR` is the project folder, so the hooks of #222 can find `ops/flow.toml` there;
- the skill is named `agent-flow:flow-probe`, and it found its script through the base directory Claude Code gives a loaded skill.

### 3. Cache path and versions

```
installPath: /Users/hungle/.claude/plugins/cache/ai-training/agent-flow/0.1.0
```

After a version bump on the branch:

```
$ claude plugin marketplace update ai-training
✔ Successfully updated marketplace: ai-training
$ claude plugin update agent-flow@ai-training
✔ Plugin "agent-flow" updated from 0.1.0 to 0.1.1 for scope user. Restart to apply changes.
$ ls ~/.claude/plugins/cache/ai-training/agent-flow
0.1.0
0.1.1
```

The path is `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` and **changes with every version**. The old version's folder stays on disk, and `claude plugin uninstall` also leaves the cache folders in place.

### 4. A Bash allow rule for a skill's script

Each rule was given to `claude -p` with `--allowedTools`. In `claude -p`, a command that no rule allows is refused ("This command requires approval"). In the table, `<cache>` is `/Users/hungle/.claude/plugins/cache/ai-training/agent-flow`.

| Rule | Command | Result |
|---|---|---|
| none | `python3 <cache>/0.1.0/skills/flow-probe/probe.py` | refused |
| `Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/flow-probe/probe.py)` | the same | refused: the variable is not expanded in a rule |
| `Bash(python3 <cache>/*/skills/flow-probe/probe.py)` | `python3 <cache>/0.1.0/skills/flow-probe/probe.py` | ran |
| the same | `python3 <cache>/0.1.0/skills/flow-probe/other.py` | refused |
| the same | `python3 <cache>/0.1.0/../../../../../../../../<another folder>/skills/flow-probe/probe.py` | **ran a script outside the plugin** (it printed `ESCAPED`) |
| `Bash(python3 <cache>/0.1.0/skills/flow-probe/probe.py)` | that escape path | refused |

**Answer: no rule shape both survives a version change and allows only the plugin's script.**

- A `*` for the version also matches `..`, so it lets any script named `skills/<skill>/<script>.py` anywhere on the disk run without a prompt.
- A rule with the exact version is safe, but it stops matching at the next `plugin update`, and until it is changed it still points at the old version's folder, which stays on disk.

So #223 keeps those scripts' rules as `ask`, never wider, as the spec says.

### Cleanup

After the probe, the plugin was uninstalled (`claude plugin uninstall agent-flow@ai-training`), the marketplace removed (`claude plugin marketplace remove ai-training`), and the leftover `~/.claude/plugins/cache/ai-training` deleted. Nothing of the probe is installed on the Mac mini.
