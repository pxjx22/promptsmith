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

### Cross-Claude guards (all Claude models)
- **Prevent file sprawl:** Explicitly instruct Claude not to create extra markdown summaries, helper scripts, or scratch files in the repository root ("Only create files directly required for the task; do not generate standalone explanation docs or scratch notes").
- **Anti-test-gaming:** Instruct the model to write general solutions rather than hardcoding to test fixtures ("Implement a general solution; do not hard-code logic to pass specific test cases").
- **XML tag hierarchy:** Put long input data/documents at the TOP, query and instructions at the BOTTOM.
- **Project rules:** `CLAUDE.md`.

## Codex (GPT-5.6 series via Codex CLI: gpt-5.6-terra, gpt-5.6-sol, gpt-5.6-luna)

Codex runs GPT-5.6 models tuned for long-running autonomous agency and tool efficiency:

- **Autonomy posture:** Optimized for deep, multi-hour autonomous execution. Set the stance: "Act as an autonomous senior engineer — proactively gather context, plan, implement, test, and refine without waiting for additional prompts at each step. Bias to action; make reasonable assumptions; only stop with questions if truly blocked. Every turn ends with a concrete edit or an explicit blocker."
- **Preambles vs Upfront plans:** GPT-5.6 supports concise preambles/developer commentary naturally (1–2 sentences every few steps). However, do **not** ask for a rigid upfront plan or heavy status narration during rollout, as this risks early stopping before execution completes.
- **Solver tools & parallelism:** Strict solver tool priority (`rg` over grep, `apply_patch` for single-file edits, dedicated `git` tool over raw shell). Maximize parallel tool calls (`multi_tool_use.parallel`) for reads and searches.
- **Strict error handling:** Bar broad try/catch blocks, silent fallbacks, or early returns without proper logging ("Propagate or surface errors explicitly rather than swallowing them; do not add success-shaped fallbacks").
- **Dirty worktree safety:** Explicitly instruct the model to respect uncommitted changes ("You may be in a dirty git worktree. Never revert changes outside the immediate scope of this task. Never run destructive git commands like `reset --hard` or `checkout --`").
- **Code review requests:** Codex defaults to findings-first, severity-ordered, with exact file:line citations and testing gaps.
- **Compaction resilience:** For tasks spanning hours, instruct Codex to persist checkpoint state in structured files or tests.
- **Project rules:** `AGENTS.md` (merged hierarchically from root to cwd).
- *Settings, not prompt text:* `model_reasoning_effort` ("medium" for daily interactive work, "high" / "xhigh" for complex debugging or architecture).

## agy (Antigravity CLI 2.0, Gemini 3.8 models)

Antigravity operates with local tooling, TUI interactive buffers, and native plan artifacts:

- **Verification loops are #1:** Provide concrete local test / build / lint commands; the agent automatically runs them and iterates on outputs.
- **Phased work produces Plan Artifacts:** "Explore how X works. Write an implementation plan artifact. Once I approve it, apply the edits and run the verification command."
- **Context hydration:** Reference files with `@path` to trigger the interactive path suggestion overlay. For UI, rendering, or styling issues, paste screenshots or screen recordings directly into the prompt using `ctrl+v`.
- **Interactive multiline buffers:** When composing complex briefs in the terminal, press `ctrl+g` to open `$EDITOR`, use `Shift+Enter` (or trailing `\`) for clean newlines, and press `esc` for instant turn cancellation.
- **Scripting with `-p`:** For automated git hooks or CI scripts, write one-shot self-contained prompts: `agy -p "<prompt>" --cwd $(pwd)`.
- **Parallel subagent fan-out:** For large sweeps or multi-module refactoring, instruct agy to dispatch background subagents: "Spawn parallel subagents to inspect [modules] concurrently."
- **Project rules:** `GEMINI.md` or `AGENTS.md` at workspace root.
- *Settings, not prompt text:* Filesystem containment and tool permissions live in `~/.gemini/antigravity-cli/settings.json` (`request-review`, `proceed-in-sandbox`, `strict`).

## Other / unknown harness

Cursor, Cline, Aider, Copilot, a raw API loop, or anything unnamed: write to the common core above. The per-harness sections mostly reduce to two questions — **(a) does this harness want progress narration in the prompt, and (b) how autonomous is its default posture?** If you can't answer those, assume "no extra narration" and "moderately autonomous" and move on.
