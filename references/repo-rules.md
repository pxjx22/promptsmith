# Repository Rules & System Instructions

A guide and template for crafting or refining persistent instruction files:
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or agent system prompts.

Because these rules are injected into every turn (or loaded hierarchically),
brevity and signal density are critical. Do not write generic programming tutorials
or restate what the model already knows. Focus strictly on project invariants,
safety boundaries, and non-obvious environment gotchas.

## Tool Discovery Matrix

| File | Target Tools | Discovery & Scope | Precedence Hierarchy |
| :--- | :--- | :--- | :--- |
| **`AGENTS.md`** | Codex, agy, Claude Code | Hierarchical (root -> cwd). Universal standard for multi-tool setups. | Subdirectory > Root |
| **`CLAUDE.md`** | Claude Code | Walked up to project root. Checked into repo. | Root (`CLAUDE.md`) |
| **`GEMINI.md`** | Antigravity (agy), Gemini CLI | Walked up to repo root, subdirectories, or global `~/.gemini/GEMINI.md`. | Subdirectories > Workspace Root > Extensions > Global (`~/.gemini/`) |
| **`PLANS.md`** | Codex, agy | Referenced in `AGENTS.md` or `.planning/`. Living ExecPlan for multi-hour autonomy. | Working Plan > Root Guidelines |
| **`DEEPSEEK.md` / `AGENTS.md`** | DeepSeek (V3/R1 via Cline, Roo, SGLang) | Root or user prompt injection. 64-token boundary alignment. | User Turn Envelope (R1) / Root System Prompt (V3) |

> **Context Precedence & Override Boundaries:**
> - **Google Gemini / agy:** Contextual instructions override default operational behaviors (e.g. style, architectural conventions, tool choices) defined in system prompts, but **cannot** override Core Mandates regarding safety, security, and agent integrity.
> - **OpenAI / Codex:** In modern reasoning models (o1/o3/GPT-5+), instructions must be passed via `developer` role messages rather than legacy `system` roles to maintain steering authority over user turns and prevent prompt injection. Multi-step projects stay grounded when pairing `AGENTS.md` with a self-contained ExecPlan (`PLANS.md`).
> - **DeepSeek:** For `deepseek-reasoner` (R1), bundle repository rules directly into user turns (Zero System Prompt contract); for `deepseek-chat` (V3), use root system prompts. Maintain byte-for-byte static prefixes aligned to 64-token blocks for API caching.

## Question Pool (at most 4, one round)

1. **Target file & tools** — `AGENTS.md` (cross-tool), `CLAUDE.md` (Claude Code only), or `GEMINI.md` (agy / Gemini CLI)?
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
- <Model quirks: never add trailing space after "Assistant:" in DeepSeek prompt templates; enforce temperature=0.6 for R1 reasoning.>
- <Date or serialization formats: e.g., timestamps MUST be YYYY-MM-DD HH:MM:SS.>

## Coding Invariants

- Error handling: Propagate errors explicitly; no broad try/catch or silent fallbacks.
- Architecture: Prefer minimal dependencies and reuse existing helpers in `<path>`.
- Style: Match existing repo patterns; avoid unnecessary abstractions.
```

## Template: Antigravity / Gemini CLI `GEMINI.md`

```markdown
# <Project / System Name>

<1–2 sentences: architectural purpose, primary language/runtime, and environment.>

## Engineering Standards

- **Directives vs. Inquiries:** Treat requests without explicit action verbs as Inquiries (analysis only); never modify files until an unambiguous Directive is given.
- **Empirical Reproduction:** For bugfixes, reproduce the failure with a new test case or script before applying fixes.
- **Type Safety & Integrity:** Do not use suppressions (`@ts-ignore`, linter disable comments, unchecked casts) or reflection hacks; write idiomatic type guards and explicit interfaces.
- **Post-Edit Silence:** Do not echo full files or provide verbose summaries after edits unless explicitly requested.

## Verification & Workflow

- Test command: `<cmd>` (run and verify passes after every change).
- Build & Lint: `<cmd>`.
- Plan Artifacts: Write complex plans to `<brain>/<session>/` or `.gemini/plans/` rather than dumping to active chat.

## Subagent Delegation Mandates

- Delegate repetitive batch tasks (>3 files) or high-volume commands (full test suites, builds) to background sub-agents to preserve parent context tokens.
- NEVER spawn parallel sub-agents that mutate the same files or shared resources.

## Git Protocol

- Do not stage or commit without explicit instructions; never use `git add .` or `git add -A`.
- Inspect state with `git status && git diff HEAD && git log -n 3`. Propose commit messages focusing on *why*.
```

## Best Practices & Context Tax Discipline

1. **Strict Context Budget (<120 lines / ~800 tokens):** Rule files are injected into *every single turn* of an agent session. A 500-line rule file costs 15,000+ input tokens over a 25-turn session. Keep root rules minimal and dense.
2. **Hierarchical Rule Offloading:** Do not put frontend, backend, and deployment rules into a single giant root file. Offload domain-specific rules to directory-level `AGENTS.md` (e.g. `frontend/AGENTS.md`), which tools discover when working in those subtrees.
3. **State the *why* for rules:** Models generalize reasons to unstated edge cases. Bare bans ("never do X") invite clever but flawed workarounds.
4. **Prioritize the non-obvious:** Put commands, gotchas, and quirks that the model cannot deduce from reading package manifests.
5. **Consolidate hard barriers:** Group non-negotiables under `## Hard Rules` so the model treats them as inviolable guardrails without wading through discursive paragraphs.
