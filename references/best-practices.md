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

---

## 5. Sampling Controls (Google Whitepaper)

Match sampling parameters to the task archetype:
- **Deterministic / Reasoning (Code, Math, Extraction, Schema JSON, Forensics):**
  * `temperature = 0.0` or `0.2`
  * Greedy decoding ensures reproducible, logically sound execution.
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
- **agy (Antigravity 2.0 / Gemini 3.8):**
  * Verification loop is primary.
  * Phased work produces native **Implementation Plan Artifacts**.
  * Context hydration: `@path` autocompletion and visual evidence pasting (`ctrl+v`).
  * Multiline `$EDITOR` (`ctrl+g`), `Shift+Enter`, `\`, and `esc` cancellation.
  * Subagent fan-out for concurrent sweeps; `-p` for one-shot CLI automation.

---

## 9. Token Efficiency & Context Architecture (2026 Research)

**The "Cache Invalidation Paradox" & Prefix Invariance (TokenPilot, 2026):**
Why: In agentic loops, naive string pruning breaks prompt layout and invalidates cached KV tensors, increasing latency and cost. Maintaining byte-for-byte static prefixes yields 50%–90% cost reductions across Anthropic, OpenAI, and Google.
- Invariant structure: `[Static System Instructions & Rules] -> [Tool Definitions] -> [Cached Base Prompt] -> [Dynamic Inputs / User Query at BOTTOM]`.
- Keep YAML frontmatter static; never place dynamic timestamps, Git SHAs, or session IDs in prompt headers.

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

**Repository Rules Context Tax:**
Why: `AGENTS.md` and `CLAUDE.md` are injected on *every turn*. Over a 25-turn session, a 500-line rule file costs 15,000+ extra input tokens.
- Keep root rules concise (<120 lines / ~800 tokens). Push domain-specific rules down into subdirectories or invoke them via on-demand skills.


