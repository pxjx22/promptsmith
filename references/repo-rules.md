# Repository Rules & System Instructions

A guide and template for crafting or refining persistent instruction files:
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or agent system prompts.

Because these rules are injected into every turn (or loaded hierarchically),
brevity and signal density are critical. Do not write generic programming tutorials
or restate what the model already knows. Focus strictly on project invariants,
safety boundaries, and non-obvious environment gotchas.

## Tool Discovery Matrix

| File | Target Tools | Discovery & Scope |
| :--- | :--- | :--- |
| **`AGENTS.md`** | Codex, agy, Claude Code | Hierarchical (root -> cwd). Universal standard for multi-tool setups. |
| **`CLAUDE.md`** | Claude Code | Walked up to project root. Checked into repo. |
| **`GEMINI.md`** | Antigravity (agy) | Walked up to repo root or workspace settings. |

## Question Pool (at most 4, one round)

1. **Target file & tools** — `AGENTS.md` (cross-tool), `CLAUDE.md` (Claude Code only), or `GEMINI.md` (agy)?
2. **Core stack & verification commands** — Primary language, build command, test command, and linter?
3. **Hard safety rules** — What actions must NEVER be run without explicit confirmation (destructive git, firewall, remote SSH, migrations)?
4. **Environment gotchas & quirks** — Aliased tools (e.g. `sed` -> `sd`), OS-specific service names (Arch `sshd` vs Debian `ssh`), hardware hazards, or strict formatting constraints?

## Template: Universal `AGENTS.md`

```markdown
# <Project / Hostname>

<1–2 sentences: what this codebase/system is, target OS/environment, and primary purpose.>

## Hard Rules

- NEVER run destructive commands (<e.g., git reset --hard, rm -rf, drop table>) without explicit confirmation.
- NEVER modify <critical configs, e.g., firewall, auth, network> without showing the full diff first.
- Always explain the *why* behind architectural decisions and recommendations — not just the what.
- <Any boundary that must never be violated without human review.>

## Workflow & Verification

- Test command: `<cmd>` (run and verify passes after every change).
- Build / Lint: `<cmd>`.
- When multiple steps depend on each other, call out the execution order and how to test between steps.
- <Git workflow: atomic commits, branch conventions, PR formats.>

## Gotchas & Local Quirks

- <Tool substitution: e.g., sed is sd on this box; use /usr/bin/sed for scripts.>
- <Platform differences: e.g., Arch uses sshd.service, Debian uses ssh.service.>
- <Kernel or hardware traps: e.g., avoid bare sensors calls, ASPM bugs.>
- <Date or serialization formats: e.g., timestamps MUST be YYYY-MM-DD HH:MM:SS.>

## Coding Invariants

- Error handling: Propagate errors explicitly; no broad try/catch or silent fallbacks.
- Architecture: Prefer minimal dependencies and reuse existing helpers in `<path>`.
- Style: Match existing repo patterns; avoid unnecessary abstractions.
```

## Best Practices for Repo Rules

1. **Keep it under 100 lines:** Bloated rule files waste context tokens on every turn and dilute instruction-following attention.
2. **State the *why* for rules:** Models generalize reasons to unstated edge cases. Bare bans ("never do X") invite clever but flawed workarounds.
3. **Prioritize the non-obvious:** Put commands, gotchas, and quirks that the model cannot deduce from reading package manifests.
4. **Distinguish hard barriers from soft preferences:** Group non-negotiables under `## Hard Rules` so the model treats them as inviolable guardrails.
