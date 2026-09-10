# Prompt-Engineering Master Cheatsheet

> Last verified: 2026-09-07, synthesized from:
> - Google DeepMind & Google Cloud: Prompt Engineering Whitepaper (Boonstra, Gulli, Cao, Nawalgaria), Step-Back Prompting (Zheng et al.) & Scaling Test-Time Compute (Snell et al.)
> - Anthropic: "Building Effective Agents" & Claude 5-Series Guides (Fable 5.1, Opus 5, Sonnet 5)
> - OpenAI: Codex Prompting Guide & GPT-6 Astra / GPT-5.6 Sol Architectures
> - Academic Frontier Research: TokenPilot (Cache Invalidation Paradox, arXiv:2606.17016), Lost in the Middle (Liu et al.), SWE-agent (ACI Stream Filtering, Yang et al.), MemGPT (Virtual Context Paging, Packer et al.)
> - Antigravity: AGY CLI 2.0 & Gemini 3.8 / 3.1 Best Practices

---

## 1. Clarity, Structure & Framing

**Be explicit about the output and the bar.**
Why: Modern frontier models do not infer "above and beyond" from terse asks.
- Weak: `Create an analytics dashboard`
- Strong: `Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation.`

**Instructions over Constraints (Positive Framing).**
Why: Models follow affirmative directions far more reliably than walls of negative prohibitions ("don't do X"), which they bypass under edge conditions.
- Weak: `Do not write fragmented bullet points and never use markdown.`
- Strong: `Write in clear, flowing prose using complete paragraphs and sentences. Reserve formatting primarily for inline code and code blocks.`

**Sequential steps as a numbered list when order matters.**
Why: Prose instructions allow models to merge, reorder, or skip intermediate steps.

**Give the motivation (*why*) behind a rule.**
Why: The model generalises from the rationale to unstated edge cases.
- Weak: `NEVER use ellipses.`
- Strong: `This text will be read aloud by a text-to-speech engine, so never use ellipses — the engine cannot pronounce them.`

**Structure mixed prompts with XML tags.**
Why: Unambiguous separation of instructions, context, documents, and examples.
- Standard tags: `<role>`, `<context>`, `<document>`, `<instructions>`, `<examples>`, `<output_format>`.

**Instruction Hierarchy & Role Precedence (OpenAI Harmony):**
Why: Modern reasoning models enforce an explicit instruction hierarchy: `system` > `developer` > `user` > `assistant` > `tool`.
- Use `developer` messages for authoritative behavioral contracts, operational rules, and tool descriptions.
- In reasoning models (o1/o3/GPT-5+), developer instructions supersede conflicting user turns and resist prompt injection.

---

## 2. Long Context, Grounding & Prompt Caching

**Put reference documents/data at the TOP, instructions at the BOTTOM.**
Why: Attention and instruction following improve measurably when queries and tasks appear at the end of long contexts (queries-at-end can boost adherence by up to 30%).

**Prompt Caching Prefix Hygiene:**
Why: Static context at the top of the prompt hits the KV cache, slashing latency by up to 80% and cost by 90%.
- Keep system instructions, repository rules, and static schema definitions byte-for-byte identical at the prompt root.
- Place variable inputs (`{{INPUT}}`) after the static prefix.

**Wrap documents with rich metadata tags.**
Why: Prevents context bleeding across multiple sources and enables clean citations.
- `<document index="1"><source>auth_service.py</source><content>...</content></document>`

**Ask for grounding quotes before generating answers.**
Why: Forcing the model to quote exact passages first anchors its attention and drastically curtails hallucinations.
- `First quote the exact passages relevant to the question, then synthesize your answer.`

---

## 3. Reasoning, Thinking & Abstraction

**Step-Back Prompting (DeepMind):**
Why: Asking a model to identify the underlying domain principle, physics law, or architectural invariant *before* solving a concrete instance dramatically improves reasoning accuracy and eliminates tunnel-vision on symptoms.
- `First, consider the broader architectural mechanics: how does connection pooling handle socket exhaustion under HTTP/2 multiplexing? Then, analyze why worker threads are wedged in TIMED_WAIT.`

**Adaptive Thinking Calibration (2025/2026):**
- On **Claude Fable 5.1 & Mythos 5.1**, thinking is always on (adaptive). Calibrate reasoning depth with the `effort` parameter.
- On **Claude Opus 5**, thinking is on by default. However, verbosity runs high: explicitly instruct conciseness in the prompt text if brevity is needed.
- On **Codex (GPT-5.6)**, tune `model_reasoning_effort` in config ("medium" for interactive tasks, "high" / "xhigh" for deep audits).

**Overthinking Damping:**
Why: Frontier reasoning models can over-explore, inflate thinking tokens, and delay execution.
- `When deciding how to approach a problem, choose an approach and commit to it. Avoid revisiting decisions unless you encounter new information that directly contradicts your reasoning.`

**CoT Damping on Native Reasoning Models (OpenAI o1, o3, GPT-5+):**
Why: Models with native test-time compute already deliberate internally. Adding external CoT pressure creates conflicting reasoning loops and degrades performance.
- Weak: `Think step by step and show your inner chain of thought before acting.`
- Strong: `Solve the problem directly. Comply with all stated constraints and run tests to verify.`
- Rule: Never prompt native reasoning models with manual chain-of-thought phrases ("think step by step").
- Tool Constraints: Front-load escaping rules, negative constraints, and boundaries at the very beginning of tool parameter descriptions (+6% accuracy gain).

**Anti-Laziness & Premature Promise Directives:**
Why: Reasoning models can occasionally promise future action or claim work is underway in the background.
- Include: `Do NOT promise to call a function later. If a function call is required, emit it now; otherwise respond normally.`

**Reasoning Model Zero-Shot Mandate & Output Tail Directives (DeepSeek-R1 & o-series):**
Why: Models trained via large-scale RL (GRPO) explore reasoning trees dynamically. Empirical research demonstrates that few-shot CoT exemplars consistently degrade performance by constraining search and inducing shortcut bias.
- Weak: Providing 3 few-shot math reasoning examples with manual step-by-step thoughts before the problem.
- Strong: Presenting a direct zero-shot problem statement with format instructions placed at the prompt tail (`Please reason step by step, and put your final answer within \boxed{}.`).
- Thinking Bypass Trigger: If a reasoning model bypasses its thinking block on simple turns (`<think>\n\n</think>`), prefill the assistant response with `<think>\n` to force test-time deliberation.

---

## 4. Examples (Few-Shot & Many-Shot)

**Few-Shot Class Balancing & Label Permutation (Google Whitepaper & Zhao et al.):**
Why: Models suffer from majority-label and recency bias. If examples end with the same class or follow a repetitive sequence, the model overfits to the order rather than semantic features.
- Provide 3–5 diverse examples.
- Ensure all target classes are balanced across examples.
- Randomize/mix the order of labels across the example list.
- Mark generated examples clearly: `<!-- example — replace with real case -->`.

**Many-Shot In-Context Learning (Anthropic 2024/2025):**
Why: In 100k+ token context windows, providing 20–50+ real-world examples reliably overrides strong model priors and locks complex formatting or classification schemas that few-shot prompts fail to enforce.

**The Few-Shot Degradation Paradox on RL Models:**
Why: While standard instruction models benefit from few-shot and many-shot exemplars, pure reasoning models (DeepSeek-R1) suffer performance regression under few-shot prompting.
- Rule: Use few-shot/many-shot for classification, extraction, and style mimicry on standard models (Claude Sonnet, Gemini Flash, DeepSeek-V3).
- Rule: Use strict zero-shot for reasoning-heavy tasks on native reasoning models (DeepSeek-R1, o1, o3).

---

## 5. Sampling Controls (Google Whitepaper)

Match sampling parameters to the task archetype:
- **Deterministic / Reasoning (Code, Math, Extraction, Schema JSON, Forensics):**
  * `temperature = 0.0` or `0.2` (for standard LLMs: Claude, GPT-4o, Gemini 3.8 Flash, DeepSeek-V3). Greedy decoding ensures reproducible, logically sound execution.
  * **Reasoning Model Exception (DeepSeek-R1 / o-series):** Mandate `temperature = 0.6` (range 0.5–0.7). Setting $T=0.0$ or using greedy decoding on RL reasoning models triggers severe degeneration (endless repetition loops, early thinking truncation).
- **Exploratory / Creative (Ideation, Copywriting, Brainstorming):**
  * `temperature = 0.7 – 1.0`, `top_p = 0.8 – 0.95`
  * Encourages lexical diversity and creative variations.

---

## 6. Agentic Workflows & Multi-Hour Autonomy

**Verification Loop is the #1 Reliability Lever (Universal):**
Why: An agent that executes tests/builds and reads outputs self-corrects; an agent without execution tools is guessing.
- `After applying edits, run <test command> and iterate on the output until it passes.`

**Context Compaction Resilience (2025/2026):**
Why: Modern agent harnesses (Codex CLI, Claude Code) automatically compact context to sustain multi-hour sessions.
- `Your context window will be automatically compacted as it approaches its limit. Do not stop tasks early due to token budget concerns. Save progress and checkpoint state to memory or structured test files before context refreshes.`

**State Management for Long Runs:**
- Use structured formats (`tests.json`, `status.json`) for machine-verifiable task states.
- Use freeform markdown (`progress.txt`) for narrative notes.
- Use git commits for atomic checkpoints.

**Guard Against File Proliferation:**
Why: 2025/2026 models tend to litter the repo with unrequested summary files and scratchpads.
- `Only create files directly required for the task. Do not create unprompted markdown summaries, helper scripts, or scratch files in the repository root.`

**Guard Against Over-Engineering:**
- `Only make changes directly requested or clearly necessary. A bug fix does not need surrounding code cleaned up. Do not add abstractions, configurability, or defensive code beyond the immediate task.`

**Guard Against Test-Gaming:**
- `Implement a general solution for all valid inputs, not just the test fixtures. Do not hard-code logic to pass specific assertions. If a test looks wrong, say so instead of working around it.`

**Subagent Delegation Calibration:**
Why: Modern models can over-delegate to subagents when a single fast tool call would suffice.
- `Use subagents only when tasks can run in parallel, require isolated context, or involve independent workstreams. For simple tasks, sequential operations, or single-file edits, work directly.`

---

## 7. Frontend & UI Design

**Avoid Generic AI Aesthetic:**
- Adhere to existing design system tokens, typography scales, and component libraries.
- Implement comprehensive interaction states: default, hover, active, focus-visible, disabled, loading, empty, and error.
- Use realistic domain data rather than "Lorem Ipsum" or generic placeholders.
- Hydrate UI debugging with visual evidence: attach screenshots or screen recordings directly (`ctrl+v`).

---

## 8. Harness Summary Cheatsheet

- **Claude Code (Fable 5.1, Opus 5, Sonnet 5):**
  * Fable 5.1: explicitly request progress updates between tool calls; do not tell it to be brief.
  * Opus 5: explicitly demand conciseness; omit redundant verification instructions.
  * Sonnet 5: literal instruction following; high frontend defaults.
  * Enforce file-sprawl and anti-test-gaming guardrails.
- **Codex (GPT-5.6 series: terra, sol):**
  * Set autonomous senior-engineer posture.
  * Natural 1–2 sentence preambles (Phase metadata: `commentary` vs `final_answer`).
  * Omit rigid upfront plans that risk early stops.
  * Solver tools first (`rg`, `git`, `apply_patch` with CFG); parallel tool calls (`multi_tool_use.parallel`).
  * Strict error handling; protect dirty worktrees.
- **agy & Gemini CLI (Antigravity 2.0 / Gemini 3.8):**
  * Directives vs Inquiries: imperative action verbs required; inquiry phrasing triggers read-only advisory mode without file edits.
  * Sub-Agents as Context Compressors: delegate batch tasks (>3 files) and verbose tool outputs (builds, test runs) to collapse multi-turn tool loops into single summary blocks.
  * Concurrency safety: parallel subagents strictly for independent read-only sweeps; never mutate shared files in parallel.
  * Explain Before Acting: concise 1-sentence intent before tool execution; strict silence post-edit.
  * Context Precedence: Subdirectories > Workspace Root (`GEMINI.md`) > Extensions > Global (`~/.gemini/GEMINI.md`).
  * Phased work produces native **Implementation Plan Artifacts**.
  * Context hydration: `@path` autocompletion and visual evidence pasting (`ctrl+v`).
  * Multiline `$EDITOR` (`ctrl+g`), `Shift+Enter`, `\`, and `esc` cancellation.
  * Verification loop is primary; `-p` for one-shot CLI automation.
- **DeepSeek (DeepSeek-V3 & DeepSeek-R1 via API / SGLang / vLLM):**
  * Dual-Model Pattern: use `deepseek-chat` (V3) for outer agent orchestration, tool use, and file editing; delegate hard reasoning/math/forensics to `deepseek-reasoner` (R1) in zero-shot sub-calls.
  * Zero-Shot Mandate for R1: never provide few-shot CoT exemplars; place format constraints (`\boxed{}`) at the prompt tail.
  * Zero System Prompt for R1: bundle instructions into user turns; system role is reserved for V3.
  * Sampling: $T=0.6$ for R1 reasoning (avoid $T=0.0$ greedy decoding loops); $T=0.0$ for V3 deterministic code editing.
  * Trailing space rule: never leave a space after `Assistant:` in prompt templates.
  * 64-token prefix caching: align static prefixes to 64-token blocks for 90% discount.
- **GLM-5.3 & GLM-5.3-Flash (Z.ai GLM Coding Plan / Claude Code / Cline / Codex):**
  * Mandatory Reasoning: always-on `thinking: {type: "enabled"}`; calibrate via `reasoning_effort` (`low`, `high`, `max` — default `max` for software engineering).
  * Dual-Protocol Drop-In: OpenAI `/coding/paas/v4` for Cline/Cursor, Anthropic `/anthropic` for Claude Code (`[1m]` suffix, `CLAUDE_CODE_AUTO_COMPACT_WINDOW: 1000000`), `/v1` for Codex.
  * Token Efficiency: ~50,000 tokens/task on Code Bench (High) at 31.4% accuracy vs Opus 4.8 at 29.5% with ~120,000 tokens; 1M context with automatic implicit caching.
  * 4-Element Task Framework: structure briefs with Goal, Context, Constraints, and Done When (observable test verification).
  * Sampling: $T=1.0$ for reasoning search; do not micromanage with manual CoT incantations.
  * Streaming deltas: isolate `delta.reasoning_content` from `delta.content` to keep tool call buffers clean.

---

## 9. Token Efficiency & Context Architecture (2026 Research)

**The "Cache Invalidation Paradox" & Prefix Invariance (TokenPilot & Anthropic):**
Why: In agentic loops, prompt caching is a strict prefix match. Any single byte change anywhere in the prefix invalidates everything after it. Maintaining byte-for-byte static prefixes yields 50%–90% cost reductions across Anthropic, OpenAI, and Google.
- **Physical Wire Render Order:**
  $$\text{Tool Definitions} \longrightarrow \text{System Prompt} \longrightarrow \text{Messages / Dynamic Context}$$
  A cache breakpoint on the last block of `system` caches both `tools` and `system` together. Changing or reordering tools invalidates the entire cache.
- **Stability Ordering Hierarchy:**
  Order inputs strictly by volatility:
  $$\text{Global Static Invariants (tools/rules)} \longrightarrow \text{Session Preamble} \longrightarrow \text{Turn History} \longrightarrow \text{Dynamic Tail (timestamps, IDs, queries)}$$
- Keep YAML frontmatter and system prompts frozen; never interpolate timestamps, UUIDs, or per-request state into the prefix.
- **Mid-Conversation System Injections:**
  When operator instructions or mode switches arrive mid-conversation, append `{"role": "system", "content": "..."}` to `messages[]` (supported on modern models like Claude Opus 5, Fable 5.1, Mythos 5.1). This leaves the cached system + tool prefix untouched.
- **Turn-Scoped Reminders:**
  For per-turn steering in tool loops, use turn-scoped messages (e.g. `clear_at: "next_user_message"`). This renders the reminder for one turn then clears it without mutating history or invalidating downstream reasoning tokens.

**The 60%–70% "Fracture Zone" Compaction Trigger (Lost in the Middle, Liu et al.):**
Why: Attention and retrieval accuracy do not degrade linearly—they follow a U-curve with sharp degradation when critical context is buried in the middle 40%–70% of the window.
- Do not wait for 90%+ context capacity warnings.
- Proactively trigger compaction or checkpointing at **60% window utilization** to prevent "fracture zone" hallucination and reasoning failure.

**Agent-Computer Interface (ACI) Stream Filtering (SWE-agent, Princeton):**
Why: Unbounded terminal outputs dump 20,000+ tokens into context in a single turn. Piped stream filters cut tool output token burn by >50%.
- Enforce piped commands in briefs and scripts:
  * `<command> | head -n 30` or `<command> | tail -n 25`
  * `rg --max-count 10 <pattern>`
  * `journalctl -u <service> -n 25 --no-pager`
  * `git diff --stat` before `git diff`

**Memory Virtualization: RAM vs. Swap (MemGPT, Packer et al.):**
Why: Active conversational context is limited RAM; disk is virtually unlimited Swap.
- Decouple heavy implementation plans, extensive diffs, and research dossiers to disk artifacts (e.g. `<brain>/<session>/` or `.planning/STATE.md`).
- Pass compact file pointers (`@path`) in conversation rather than maintaining thousands of lines of documentation in active context.

**Test-Time Deliberation Damping (Scaling Test-Time Compute, Snell et al.):**
Why: Unbounded test-time deliberation hits an exponential plateau where compute scales rapidly without accuracy gains.
- On routine bugfixes and mechanical edits: `Commit to the first direct, verifiable solution. Do not evaluate alternative architectural paradigms for this fix.`
- Configure explicit reasoning ceilings: `thinkingTokenLimit: 8000` (Claude), `reasoning_effort: low` (Codex), or Gemini Thinking Level `low/medium`.

**Diff-First Output Contracts:**
Why: Asking a model to "return the updated file" causes it to output 800 lines of unchanged code, burning output tokens and bloating downstream conversational history.
- Directive: `Produce minimal, surgical diffs (unified diff format or apply_patch) or targeted line replacements; never echo unchanged code blocks.`

**Sub-Agent Context Compression (Google Gemini CLI / agy):**
Why: The main orchestrator context window is the most constrained resource. Every turn taken in the main loop permanently consumes tokens across all future turns.
- Offload high-volume tool outputs (verbose builds, full test suites), repetitive multi-file sweeps (>3 files), and speculative trial-and-error research to background sub-agents.
- Upon completion, the sub-agent's entire multi-turn tool trajectory collapses into a single summary block returned to the parent, slashing parent session token burn by up to 80%.
- Enforce strict concurrency isolation: Never spawn parallel subagents that mutate overlapping files or shared resources.

**Batch Compaction over Rolling Invalidation (OpenAI Cookbook & Realtime):**
Why: Sliding-window eviction that drops messages one turn at a time shifts the conversation prefix every turn, destroying 100% of the KV cache on every interaction.
- Strategy: Use discrete batch compaction (`retention_ratio: 0.7` or threshold-based pruning) to drop the oldest 30% in one chunk, keeping 70% of the KV cache intact across the next N turns.
- Routing Locality: Use `prompt_cache_key` to route requests to the same GPU host for cache locality (~15 RPM sweet spot per prefix), boosting cache hit rates by 8.5% and reducing token costs by up to 23%.

**Repository Rules Context Tax:**
Why: `AGENTS.md` and `CLAUDE.md` are injected on *every turn*. Over a 25-turn session, a 500-line rule file costs 15,000+ extra input tokens.
- Keep root rules concise (<120 lines / ~800 tokens). Push domain-specific rules down into subdirectories or invoke them via on-demand skills.

**Cache Granularity Thresholds by Provider:**
- **Anthropic:** 1,024-token minimum (explicit `cache_control: {"type": "ephemeral"}`).
- **OpenAI:** 1,024-token minimum (automatic prefix caching with optional `prompt_cache_key`).
- **DeepSeek:** **64-token minimum** (automatic prefix caching in 64-token blocks, up to 90% discount).

---

## 10. Prompt Cruft Auditing & Anti-Pattern Taxonomy (Anthropic 2026)

> **Prime Directive:** Distinguish cruft from load-bearing content. Every token must earn its place. Indiscriminate shortening deletes high-value context.

### The Golden Rules
1. **Context is never cruft:** Audience, product facts, quality bars, environment invariants, and the *reasons* behind constraints must stay. Too-short prompts produce generic output because models fill gaps with generic defaults.
2. **Cruft $\neq$ length:** Harm comes from specific outdated instructions that actively degrade behavior on modern reasoning models, not raw word count.

### The 4 Anti-Pattern Groups

| Anti-Pattern Group | Signals & Examples | Why It Degrades Modern Models | Correct Fix |
|---|---|---|---|
| **1. Pressure Language** | `CRITICAL: MUST`, `IMPORTANT: NEVER`, `!!`, `Be thorough, do not be lazy` | Shouting was needed for older, weakly-steerable models. On modern models, it causes over-triggering, rigid failure in edge cases, and anxious hedging. | State constraints plainly at conversational volume, accompanied by the rationale ("why"). |
| **2. Obsolete Scaffolds** | `think step by step`, `<scratchpad>`, assistant JSON prefills (`{"role": "assistant", "content": "{"`), regex extraction, `every N tool calls summarize` | Native adaptive thinking and Structured Outputs replace these completely. Hand-rolled scaffolds starve reasoning or hard-error (400) on frontier APIs. | Replace with native `thinking: {type: "adaptive"}` + `effort`, and schema-based Structured Outputs. Delete update cadences. |
| **3. Over-Specification & Prohibition Clusters** | Step-by-step choreographies for judgment tasks (`STEP 1... STEP 2...`), runs of 3+ `Do not / Never` lines without rationale | Prescriptive scripts degrade output because the model's internal plan usually beats hand-written scripts. Unmotivated prohibitions anchor the model toward the prohibited error. | Describe outcomes, boundaries, and verification criteria. Keep prohibitions only when backed by observable business/policy constraints or demonstrated failures. |
| **4. Fossils & Relics** | Model-version workarounds, "X now works differently", patch accretion, identity stubs (`You are a helpful assistant`), deprecated model strings (`gemini-1.5-*`, `gemini-2.0-*`, `gemini-2.5-*`, `claude-3-opus`, `gpt-4`), legacy SDK patterns (`google.generativeai`, `@google/generative-ai`, `generateContent`) | Text written as workarounds for retired models accumulates indefinitely, confusing modern models with phantom alternatives. | Write rules as if current rules are the only rules that ever existed. Replace identity stubs with concrete product context; upgrade model strings and APIs. |

### Trigger Text vs. Behavioral Text Split
- **Trigger/Routing Text** (skill frontmatter `description`, intent classifiers) may carry calibrated urgency, because skills currently under-trigger.
- **Behavioral Text** inside prompt instructions must explain with reasons rather than shout.

---

## 11. Tool Surface Design & Agent Architecture (Anthropic 2026)

### Bash vs. Dedicated Tools
Start with a general shell/bash tool for broad leverage. Promote an action to a **dedicated tool** only when the harness requires one of four specific invariants:
1. **Security Boundary & Gating:** Hard-to-reverse actions (sending emails, deleting tables, pushing code) can be gated behind human confirmation with typed arguments. Gating `send_email(to, subject)` is clean; gating `bash -c "curl -X POST ..."` is fragile.
2. **Staleness Checks:** An edit tool can verify that a file has not changed on disk since the model last read it, rejecting out-of-date writes.
3. **Custom UI & Interaction:** Actions that need dedicated UX (e.g. interactive multi-choice questions that block the agent loop until answered) require typed tools.
4. **Scheduling & Concurrency:** Read-only operations (`glob`, `grep`) can be flagged as parallel-safe; bash execution must serialize.

### Programmatic Tool Calling (PTC)
Instead of round-tripping every single tool call through the model context (adding latency and bloating token history with intermediate payloads):
- The model writes a short script that executes within a sandbox environment.
- The script invokes tools as functions, loops, and filters data locally.
- **Only the final output returns to the agent's context.** Token cost scales with final output rather than intermediate data.

### Tool Descriptions as "Man Pages"
- **Precision and contract accuracy over brevity:** The description must precisely state what the tool does, when to call it, when *not* to call it, parameter semantics, and caveats.
- Prescriptive trigger conditions ("Call this when...") significantly lift tool call accuracy on frontier models.
- **Never smuggle behavior into tool descriptions:** Keep worked dialogue examples, conversational instructions, and cross-tool scolding out of tool descriptions; place behavioral guidance in prompt instructions or skills.

---

## 12. Economics: Cost per Completed Task (Anthropic 2026)

Optimize spend in units of **cost per completed task, not cost per token**:
- A frontier model with higher sticker price is often cheaper overall if it solves tasks in fewer turns without cascading errors or human intervention.
- A cheaper model that fails bills its tokens, bills the retry, and bills whatever the downstream failure costs.

### The Hierarchy of Optimization Levers
Always execute **Free Wins** before **Tradeoffs**:
1. **Free Wins (Zero Quality Risk - Apply First):**
   - *Prompt Caching:* Reprices repeated multi-turn input to 0.1x (or 0.025x).
   - *Input-Token Hygiene:* Run prompt audits, remove inlined documentation, avoid passing whole file dumps.
   - *Loop Hygiene:* Prune stale tool outputs and completed thinking blocks across turns.
   - *Output-Token Hygiene:* Enforce diff-first contracts and qualitative conciseness.
   - *Batch Processing:* 50% discount for asynchronous workloads that can wait.
2. **Tradeoffs (Exchange Intelligence for Cost - Validate with Evals):**
   - *Effort tuning:* Dialing down reasoning `effort` on routine tasks.
   - *Model selection / Multi-model cascades:* Delegating narrow subtasks to smaller models while keeping coordination on the flagship.

---

## 13. Model-Based Evaluation & Rubric Engineering (OpenAI Evals)

**The `cot_classify` Gold Standard:**
Why: Direct classification (`classify`) suffers from immediate-token bias, while explanation-after-choice (`classify_cot`) fails to steer the decision token.
- Pattern:
  ```
  First, write out in a step by step manner your reasoning to be sure that your conclusion is correct.
  Avoid simply stating the correct answer at the outset.
  Then print only a single choice from {choices} (without quotes or punctuation) on its own line corresponding to the correct answer.
  At the end, repeat just the answer by itself on a new line.

  Reasoning:
  ```
- Reverse-Line Parsing: Split completion lines and parse in reverse (`lines[::-1]`) to match against valid choice strings, guaranteeing robust verdict extraction despite verbose chain of thought.

**Rubric Taxonomies:**
- **Set-Theoretic Rubric (`fact.yaml`):** Decomposes factual consistency into formal set operations: Subset ($\subseteq$), Superset ($\supseteq$), Exact Match ($=$), Factual Contradiction ($\neq$), or Inconsequential Difference ($\approx$).
- **Parametric Criteria Checking (`closedqa.yaml`):** Injects criteria strings dynamically (`{criteria: "correctness: Is the answer correct?"}`) into a standardized binary verification harness.
- **Additive Checklist Rubrics:** Sums discrete independent conditions (formatting, relevance, tone) into a composite scalar score ($0 \dots N$).

**Solver vs. SolverEval Decoupling:**
Why: Conflating benchmark tasks with agent scaffolding causes state leakage across eval runs.
- Separate task specifications (`SolverEval`) from prompt/model scaffolding (`Solver`).
- Clone solver instances per sample to guarantee clean state isolation.


