# Harness-specific notes

> Last verified: 2026-09-04, against:
> - platform.claude.com/docs/.../claude-prompting-best-practices (Claude Fable 5.1, Opus 5, Sonnet 5)
> - developers.openai.com/cookbook/.../codex_prompting_guide (GPT-5.6 series: terra, sol, luna)
> - antigravity.google/docs/cli/best-practices (Antigravity CLI 2.0 / Gemini 3.8)
> Model-version-specific claims below age fast — flag anything that looks stale to the user.

When a coding brief targets a known agent harness, tune the prompt to its
conventions. When the harness is unknown, write to the common core and skip the
harness-specific levers.

## Common core (all harnesses)

- **Verification loop.** Give a concrete test / build / lint command and tell
  the agent to run it and iterate until it passes. This is the single biggest
  reliability lever across every harness. If no tests exist, ask the agent to
  write one first.
- **Point, don't paste.** The agent can read the repo — name the files, dirs,
  and symbols in scope instead of pasting long excerpts.
- **Explicit action verbs** ("implement", "change", "add") and an observable
  done-criteria.
- **Anti-slurp tool bounds.** Instruct the agent to use targeted searches (`rg -n -C 1`, `git diff --stat`) and line ranges; bar reading full files exceeding 150 lines without bounds.
- **Diff-first output contract.** Produce minimal unified diffs or patch payloads; never echo back unmodified files.
- **Scope ceiling** — "don't refactor unrelated code, don't add abstractions or
  dependencies the task doesn't need".
- **Phased for complex work:** explore → plan → (user approves) → execute.

## Claude Code (Claude models: Fable 5.1, Opus 5, Sonnet 5)

Current Claude models share strong XML structure affinity and instruction following, but diverge on verbosity and loop narration:

### Claude Fable 5.1 & Mythos 5.1
- **Thinking is always on (adaptive):** It cannot be disabled; it dynamically calibrates based on `effort` and task complexity.
- **Progress visibility:** Fable 5.1 tends to write *fewer* user-facing progress updates between tool calls during long agentic runs. If you want progress visibility, ask explicitly ("post a short progress note every few tool calls") and never instruct it to keep progress updates terse.
- **Less default chat formatting:** Fable 5.1 formats less than older models; over-specifying negative formatting rules (e.g. "no markdown headers") can strip structure the output genuinely needs.
- **Append-only history:** Pass thinking blocks back unchanged; do not edit prior turns mid-stream.

### Claude Opus 5
- **The verbosity exception:** Default user-facing responses run longer than other models, and raising or lowering reasoning effort does *not* reliably shorten response length. When brevity matters, you must explicitly demand conciseness in the prompt text.
- **Built-in self-correction:** Opus 5 already self-verifies thoroughly. Avoid piling on repetitive "verify your work 5 times" instructions or it will over-verify and loop unnecessarily.

### Claude Sonnet 5
- **Literal instruction following:** Follows constraints to the letter — ensure negative constraints are airtight, or preferably phrased as positive bounds.
- **High frontend defaults:** Produces polished, accessible, responsive UI code out of the box without needing basic layout hand-holding.

### Cross-Claude guards & Token Architecture
- **Context Budget & Auto-Compact:** 200,000-token working limit. Claude Code automatically reserves a 16.5% buffer (~33,000 tokens) for auto-compaction (`CLAUDE_CODE_AUTO_COMPACT_WINDOW`).
- **Proactive Compaction:** Use targeted manual compaction around 50%–60% usage before hitting the "fracture zone": `/compact focus on <core module>, omit closed test traces`.
- **Reasoning Token Cap:** Bound test-time deliberation in `~/.claude/settings.json`:
  ```json
  {
    "model": "claude-sonnet-5",
    "thinkingTokenLimit": 8000,
    "tokenBudget": { "autoCompactAt": 0.60 }
  }
  ```
- **Prefix cache stability:** Claude automatically caches prompt prefixes (90% discount, 5m sliding TTL). Keep system instructions, tools, and `CLAUDE.md` byte-for-byte identical; place dynamic inputs at the prompt tail.
- **Tool slicing:** Instruct Claude to use `view_file` with `StartLine`/`EndLine` slices rather than viewing entire files.
- **Prevent file sprawl:** Explicitly instruct Claude not to create extra markdown summaries, helper scripts, or scratch files in the repository root ("Only create files directly required for the task; do not generate standalone explanation docs or scratch notes").
- **Anti-test-gaming:** Instruct the model to write general solutions rather than hardcoding to test fixtures ("Implement a general solution; do not hard-code logic to pass specific test cases").
- **XML tag hierarchy:** Put long input data/documents at the TOP, query and instructions at the BOTTOM.
- **Project rules:** `CLAUDE.md`.

## Codex (GPT-6 Astra & GPT-5.6 series via Codex CLI)

Codex runs GPT-6 Astra (1,050,000-token context window; active execution buffer ~258k tokens) and GPT-5.6 Sol/Terra:

- **Autonomy posture:** Optimized for deep, multi-hour autonomous execution. Set the stance: "Act as an autonomous senior engineer — proactively gather context, plan, implement, test, and refine without waiting for additional prompts at each step. Bias to action; make reasonable assumptions; only stop with questions if truly blocked. Every turn ends with a concrete edit or an explicit blocker."
- **Prompt Cache Breakpoint & 30m TTL:** Codex uses a 30-minute sliding window with 50% discount on cached tokens. Ensure `prompt_cache_breakpoint = true` in config to prevent volatile tool outputs from invalidating the system prompt.
- **Reasoning Effort Tuning:** In `~/.codex/config.toml`, set `reasoning_effort = "low"` for routine feature edits and bugfixes to avoid test-time deliberation plateaus; escalate to `"medium"`/`"high"` only for deep architectural forensics.
- **Patching over rewriting:** Strict solver tool priority (`rg` over grep, `apply_patch` for single-file edits, dedicated `git` tool over raw shell). Bar full-file rewrites.
- **Preambles vs Upfront plans:** GPT-6/5.6 supports concise preambles/developer commentary naturally (1–2 sentences every few steps). Do **not** ask for a rigid upfront plan or heavy status narration during rollout, as this risks early stopping before execution completes.
- **Strict error handling:** Bar broad try/catch blocks, silent fallbacks, or early returns without proper logging ("Propagate or surface errors explicitly rather than swallowing them; do not add success-shaped fallbacks").
- **Dirty worktree safety:** Respect uncommitted changes ("You may be in a dirty git worktree. Never revert changes outside the immediate scope of this task. Never run destructive git commands like `reset --hard` or `checkout --`").
- **Project rules:** `AGENTS.md` (merged hierarchically from root to cwd).

## agy (Antigravity CLI 2.0, Gemini 3.8 & 3.1 models)

Antigravity operates with local tooling, TUI interactive buffers, and dual-layer context virtualization:

- **Context Architecture:** Gemini 3.8 Flash provides a 1,000,000-token window with a 65,536-token generation ceiling, paired with Gemini 3.1 Pro for deep reasoning.
- **Memory Virtualization (RAM vs. Swap):** Verbose tool outputs and full logs stream to `transcript_full.jsonl` on disk; active context keeps a compact stub in `transcript.jsonl`.
- **Implementation Plan Artifacts:** Write multi-step plans to persistent markdown artifacts (`<appDataDir>/brain/<session-id>/`) rather than echoing thousands of tokens of plan text into active chat context.
- **Hook Telemetry & Safe Compaction:**
  * When context reaches **$\le$ 35% remaining**: finish in-flight subtasks; do not initiate broad exploratory sweeps.
  * When context reaches **$\le$ 25% remaining**: halt execution, checkpoint status to `.planning/STATE.md`, and execute safe compaction.
- **Verification loops are #1:** Provide concrete local test / build / lint commands; the agent automatically runs them and iterates on outputs.
- **Subagent fan-out damping:** Spawn subagents only for concurrent, independent sweeps; work directly for sequential edits to avoid exponential context inflation.
- **Multimodal token budget:** When pasting screenshots or recordings (`ctrl+v`), crop to the relevant widget or UI pane rather than pasting full-screen multi-monitor canvases.
- **Context hydration:** Reference files with `@path` to trigger the interactive path suggestion overlay.
- **Interactive multiline buffers:** When composing complex briefs in the terminal, press `ctrl+g` to open `$EDITOR`, use `Shift+Enter` (or trailing `\`) for clean newlines, and press `esc` for instant turn cancellation.
- **Scripting with `-p`:** For automated git hooks or CI scripts, write one-shot self-contained prompts: `agy -p "<prompt>" --cwd $(pwd)`.
- **Project rules:** `GEMINI.md` or `AGENTS.md` at workspace root.
- *Settings, not prompt text:* Filesystem containment and tool permissions live in `~/.gemini/antigravity-cli/settings.json` (`request-review`, `proceed-in-sandbox`, `strict`).

## Other / unknown harness

Cursor, Cline, Aider, Copilot, a raw API loop, or anything unnamed: write to the common core above. The per-harness sections mostly reduce to two questions — **(a) does this harness want progress narration in the prompt, and (b) how autonomous is its default posture?** If you can't answer those, assume "no extra narration" and "moderately autonomous" and move on.
