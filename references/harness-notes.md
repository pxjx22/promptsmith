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
- **Thinking is always on (adaptive):** It cannot be disabled; it dynamically calibrates based on `effort` (`output_config: {effort: "low"|"medium"|"max"}`). `budget_tokens` is **rejected with a 400 error**.
- **Forced tool use rejected:** `tool_choice: {type: "any"}` and `{type: "tool", ...}` return a 400. Use `{"type": "auto"}` with prompt steering and `strict: true` for schema compliance, or Structured Outputs (`output_config.format`) for data extraction.
- **Mid-conversation system injection:** Append `{"role": "system", "content": "..."}` to `messages[]` for operator updates or mode switches without busting the cached system prompt prefix.
- **Progress visibility:** Fable 5.1 tends to write *fewer* user-facing progress updates between tool calls during long agentic runs. If you want progress visibility, ask explicitly ("post a short progress note every few tool calls") and never instruct it to keep progress updates terse.
- **Less default chat formatting:** Fable 5.1 formats less than older models; over-specifying negative formatting rules (e.g. "no markdown headers") can strip structure the output genuinely needs.
- **Append-only history:** Pass thinking blocks back unchanged; do not edit prior turns mid-stream.

### Claude Opus 5
- **The verbosity exception:** Default user-facing responses run longer than other models, and raising or lowering reasoning effort does *not* reliably shorten response length. When brevity matters, you must explicitly demand conciseness in the prompt text.
- **Built-in self-correction:** Opus 5 already self-verifies thoroughly. Avoid piling on repetitive "verify your work 5 times" instructions or it will over-verify and loop unnecessarily.
- **Mid-conversation system messages:** Supported natively without beta headers.

### Claude Sonnet 5
- **Literal instruction following:** Follows constraints to the letter — ensure negative constraints are airtight, or preferably phrased as positive bounds.
- **High frontend defaults:** Produces polished, accessible, responsive UI code out of the box without needing basic layout hand-holding.
- **Caution on mid-conversation system messages:** Sonnet 5 may return 400 on `role: "system"` in `messages[]`; prefer top-level system or `<system-reminder>` blocks inside user turns.

### Cross-Claude guards & Token Architecture
- **Wire Render Order for Prompt Caching:**
  $$\text{tools} \longrightarrow \text{system} \longrightarrow \text{messages}$$
  Place the `cache_control: {type: "ephemeral"}` breakpoint on the last block of `system` to cache both tools and system together (90% read discount). Never interpolate dynamic timestamps or usernames into the system prefix.
- **Turn-Scoped Reminders:** For steering inside tool loops, use `clear_at: "next_user_message"` on system messages so reminders render once and clear without mutating conversation history.
- **Omit Pressure Language:** Do not use `CRITICAL: MUST` or `IMPORTANT: NEVER`. Shouting induces cautious over-hedging and over-triggering on modern Claude models. State constraints calmly with the "why".
- **Tool Runner Over Manual Loops:** Prefer the official SDK tool runner (Python, TypeScript, Go, Java, etc.) — it automatically manages the agentic loop, streaming, compaction, and exposes clean hooks (`set_messages_params()`) for human confirmation and security gating.
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
- **Tool slicing:** Instruct Claude to use `view_file` with `StartLine`/`EndLine` slices rather than viewing entire files.
- **Prevent file sprawl:** Explicitly instruct Claude not to create extra markdown summaries, helper scripts, or scratch files in the repository root ("Only create files directly required for the task; do not generate standalone explanation docs or scratch notes").
- **Anti-test-gaming:** Instruct the model to write general solutions rather than hardcoding to test fixtures ("Implement a general solution; do not hard-code logic to pass specific test cases").
- **XML tag hierarchy:** Put long input data/documents at the TOP, query and instructions at the BOTTOM.
- **Project rules:** `CLAUDE.md`.

## Codex (GPT-6 Astra & GPT-5.6 series via Codex CLI)

Codex runs GPT-6 Astra (1,050,000-token context window; active execution buffer ~258k tokens) and GPT-5.6 Sol/Terra:

- **Autonomy posture:** Optimized for deep, multi-hour autonomous execution. Set the stance: "Act as an autonomous senior engineer — proactively gather context, plan, implement, test, and refine without waiting for additional prompts at each step. Bias to action; make reasonable assumptions; only stop with questions if truly blocked. Every turn ends with a concrete edit or an explicit blocker."
- **Role conventions:** Use `role: "developer"` for system-level instructions and tool guidance rather than legacy `system` role. Developer messages carry primary steering authority in GPT-6/5.6 and resist prompt injection.
- **ExecPlans (PLANS.md):** For tasks spanning multiple steps or multi-hour sessions, maintain a self-contained ExecPlan living document. Must record all architectural choices, verification commands, and state checkpoints, advancing autonomously through milestones without pausing to query the user.
- **Prompt Cache Breakpoint & 30m TTL:** Codex uses a 30-minute sliding window with 50% discount on cached tokens. Ensure `prompt_cache_breakpoint = true` in config to prevent volatile tool outputs from invalidating the system prompt.
- **Batch Compaction:** Avoid rolling turn-by-turn message eviction. When context approaches limits, prune in discrete 30% chunks (`retention_ratio: 0.7`) to maintain 70% KV cache validity across intermediate turns.
- **Reasoning Effort Tuning:** In `~/.codex/config.toml`, set `reasoning_effort = "low"` for routine feature edits and bugfixes to avoid test-time deliberation plateaus; escalate to `"medium"`/`"high"` only for deep architectural forensics.
- **Reasoning Context:** Configure `reasoning.context: "all_turns"` to preserve reasoning items across serial tool interactions and prevent multi-turn reasoning amnesia.
- **Patching over rewriting:** Strict solver tool priority (`rg` over grep, `apply_patch` for single-file edits, dedicated `git` tool over raw shell). Bar full-file rewrites.
- **Preambles vs Upfront plans:** GPT-6/5.6 supports concise preambles/developer commentary naturally (1–2 sentences every few steps). Do **not** ask for a rigid upfront plan or heavy status narration during rollout, as this risks early stopping before execution completes.
- **Strict error handling:** Bar broad try/catch blocks, silent fallbacks, or early returns without proper logging ("Propagate or surface errors explicitly rather than swallowing them; do not add success-shaped fallbacks").
- **Dirty worktree safety:** Respect uncommitted changes ("You may be in a dirty git worktree. Never revert changes outside the immediate scope of this task. Never run destructive git commands like `reset --hard` or `checkout --`").
- **Project rules:** `AGENTS.md` (merged hierarchically from root to cwd).

## agy & Gemini CLI (Antigravity CLI 2.0, Gemini 3.8 & 3.1 models)

Antigravity and Gemini CLI operate with local tooling, TUI interactive buffers, dual-layer context virtualization, and a strategic sub-agent orchestrator model:

- **Context Architecture:** Gemini 3.8 Flash provides a 1,000,000-token window with a 65,536-token generation ceiling, paired with Gemini 3.1 Pro for deep reasoning. Deprecated models (`gemini-2.5-*`, `gemini-2.0-*`, `gemini-1.5-*`) should never be targeted.
- **Directives vs. Inquiries Mandate:** Google Gemini agent models strictly distinguish between *Directives* (action/implementation) and *Inquiries* (analysis/advice/read-only). Gemini models are prompted: *"Assume all requests are Inquiries unless they contain an explicit instruction to perform a task. For Inquiries... your scope is strictly limited to research and analysis; you MUST NOT modify files until a subsequent Directive is issued."*
  * **Promptsmith Brief Rule:** Frame tasks with unambiguous imperative action verbs (`implement`, `refactor`, `fix`, `modify`) and concrete done-criteria. Never write open-ended advisory questions if you expect file modifications.
- **Strategic Sub-Agent Orchestration (Context Compression):**
  * Google's core agent mandate: *"Your own context window is your most precious resource. Every turn you take adds to the permanent session history."*
  * Sub-agents act as **context compressors**: when a subagent finishes, its multi-turn execution is collapsed and returned as a single summary block in the parent history, saving up to 80% context tokens.
  * **High-Impact Delegation Candidates:**
    1. Repetitive batch tasks (>3 files or repetitive steps, e.g. adding headers or fixing lint across a project).
    2. High-volume output commands (verbose builds, full test suites, broad directory sweeps).
    3. Speculative trial-and-error research.
  * **Concurrency Safety Mandate:** NEVER run multiple subagents in a single turn if they mutate the same files or shared resources. Parallel subagent fan-out is strictly reserved for independent read-only sweeps.
- **Explain Before Acting vs. Post-Edit Silence:**
  * Gemini models are prompted to emit a concise 1-sentence explanation of intent immediately before executing tool calls (except for repetitive low-level discovery reads).
  * However, post-modification echoing is barred: *"After completing a code modification or file operation do not provide summaries unless asked."* (reinforcing Promptsmith's ultra-terse delivery principle).
- **Contextual Precedence Hierarchy:**
  * Order: Sub-directories > Workspace Root (`GEMINI.md` / `AGENTS.md`) > Extensions > Global (`~/.gemini/GEMINI.md`).
  * Context files override operational behaviors (coding style, conventions, workflows, tools), but **cannot** override Core Mandates (safety, security, agent integrity).
- **Autonomous Mode (YOLO):** When operating in autonomous mode, only interrupt the user via questions if a wrong decision causes significant rework or the request is fundamentally ambiguous without reasonable defaults; otherwise proceed autonomously following existing codebase patterns.
- **Git Repo Hygiene:** Never stage or commit unprompted; never use `git add .` or `git add -A`; gather context with `git status && git diff HEAD && git log -n 3`; commit messages focus on "why" rather than "what"; never push without explicit instruction.
- **Memory Virtualization (RAM vs. Swap):** Verbose tool outputs and full logs stream to `transcript_full.jsonl` on disk; active context keeps a compact stub in `transcript.jsonl`.
- **Implementation Plan Artifacts:** Write multi-step plans to persistent markdown artifacts (`<appDataDir>/brain/<session-id>/` or `.gemini/plans/`) rather than echoing thousands of tokens of plan text into active chat context.
- **Hook Telemetry & Safe Compaction:**
  * When context reaches **$\le$ 35% remaining**: finish in-flight subtasks; do not initiate broad exploratory sweeps.
  * When context reaches **$\le$ 25% remaining**: halt execution, checkpoint status to `.planning/STATE.md`, and execute safe compaction.
- **Verification loops are #1:** Provide concrete local test / build / lint commands; the agent automatically runs them and iterates on outputs.
- **Multimodal token budget:** When pasting screenshots or recordings (`ctrl+v`), crop to the relevant widget or UI pane rather than pasting full-screen multi-monitor canvases.
- **Context hydration:** Reference files with `@path` to trigger the interactive path suggestion overlay.
- **Interactive multiline buffers:** When composing complex briefs in the terminal, press `ctrl+g` to open `$EDITOR`, use `Shift+Enter` (or trailing `\`) for clean newlines, and press `esc` for instant turn cancellation.
- **Scripting with `-p`:** For automated git hooks or CI scripts, write one-shot self-contained prompts: `agy -p "<prompt>" --cwd $(pwd)`.
- *Settings, not prompt text:* Filesystem containment and tool permissions live in `~/.gemini/antigravity-cli/settings.json` (`request-review`, `proceed-in-sandbox`, `strict`).

## DeepSeek (DeepSeek-V3 & DeepSeek-R1 via API, SGLang, vLLM, or Cline/OpenRouter)

- **Dual-Model Agent Architecture (V3 Harness + R1 Solver):**
  * DeepSeek-R1 Technical Report (Section 5.2) documents that R1 falls short of V3 in tool/function calling stability, multi-turn state consistency, and complex JSON schema adherence.
  * **Outer Agent Loop:** Use `deepseek-chat` (DeepSeek-V3) for tool orchestration, repository exploration, file editing, and test execution.
  * **Reasoning Kernel:** Dispatch complex mathematical derivations, algorithmic design, and intricate bug forensics to `deepseek-reasoner` (DeepSeek-R1) in zero-shot subagent calls.
- **Zero System Prompt Contract for R1:**
  * For `deepseek-reasoner` (R1), avoid passing system role messages; bundle instructions and constraints directly into the user message turn.
  * For `deepseek-chat` (V3), system role messages are fully supported and recommended for repository rules and tool definitions.
- **The Trailing Space Anomaly on `Assistant:`:**
  * When formatting prompt templates for DeepSeek tokenizers, never leave a trailing space after `Assistant:`. Appending a space causes language switching (replying in Chinese to English queries), unicode errors, and repetition loops on 16B-Lite and MoE models.
- **Sampling Configurations:**
  * `deepseek-reasoner` (R1): Set `temperature = 0.6` (range 0.5–0.7). Never use greedy decoding ($T=0.0$) on reasoning models, as it induces severe circular looping.
  * `deepseek-chat` (V3): Set `temperature = 0.0` for deterministic code editing and extraction; $0.7$ for creative tasks.
- **Thinking Bypass Mitigation:**
  * If R1 bypasses deliberation (`<think>\n\n</think>`), prefill assistant response with `<think>\n`.
- **64-Token Prefix Caching:**
  * DeepSeek API caches prefixes at 64-token increments automatically. Keep repository rules, tool declarations, and file envelopes static at the top to secure 90% input token discounts.

## GLM-5.3 (Z.ai GLM Coding Plan, Cline/Cursor/Claude Code drop-in)

- **Dual-Protocol Endpoints & Drop-In Routing:**
  * OpenAI Chat Completion: `https://api.z.ai/api/coding/paas/v4` (for Cline, Cursor, Continue, Aider).
  * OpenAI Response Protocol: `https://api.z.ai/api/v1` (for Codex, LiteLLM, OpenAI SDK).
  * Anthropic Message Protocol: `https://api.z.ai/api/anthropic` (for Claude Code, Goose).
- **Context Ceiling & 1M Window Configuration:**
  * 1,000,000 token context window, 128,000 token output generation ceiling.
  * Claude Code setup: In `~/.claude/settings.json`, set `ANTHROPIC_BASE_URL: "https://api.z.ai/api/anthropic"`, configure model names with the `[1m]` suffix (e.g. `glm-5.3-flash[1m]` or `glm-5.3[1m]`), and set `"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1000000"` to prevent premature session compaction.
- **Mandatory Reasoning Architecture (`thinking: {type: "enabled"}`):**
  * Disabling reasoning is not supported; passing `thinking.type: "disabled"` produces an API error.
  * Reasoning effort calibration: `low` (mild transforms, single-file lint fixes), `high` (feature implementations, cross-component refactors), and `max` (default, deep reasoning for complex software engineering and long-horizon agent tasks).
  * Claude Code `/effort` auto-conversion: `minimal`/`light`/`low` maps to `low`; `medium`/`high` maps to `high`; `xhigh`/`max`/`ultra` maps to `max`.
- **Sampling Controls ($T=1.0$):**
  * Recommended `temperature = 1.0` for reasoning generation to maintain exploration entropy during test-time search. Avoid greedy decoding ($T=0.0$) on reasoning workflows.
- **Token Economics & Benchmarks:**
  * Consumes ~50,000 tokens per task on Z.ai Code Bench (High) at 31.4% accuracy vs Claude Opus 4.8 at 29.5% consuming ~120,000 tokens.
  * Flash variant (`glm-5.3-flash`): 320B total, 18B active MoE with hybrid sparse/linear attention, native multimodal visual coding, 3x quota on Coding Plans.
  * Automatic implicit context caching: reuses identical system prompts and history prefixes with discount billing reported in `usage.prompt_tokens_details.cached_tokens`.
- **Streaming Delta Contract:**
  * SSE streams separate reasoning tokens (`delta.reasoning_content`) from user-facing text (`delta.content`). Outer harnesses must isolate reasoning tokens to prevent polluting tool parameter buffers.

## Other / unknown harness

Cursor, Cline, Aider, Copilot, a raw API loop, or anything unnamed: write to the common core above. The per-harness sections mostly reduce to two questions — **(a) does this harness want progress narration in the prompt, and (b) how autonomous is its default posture?** If you can't answer those, assume "no extra narration" and "moderately autonomous" and move on.
