# GLM-5.3 Scraping & Prompt Intelligence Reference

This directory contains scraped and curated reference material from the official Z.ai developer documentation ([`docs.z.ai`](https://docs.z.ai/guides/llm/glm-5.3)) and the [`GLM-5-3-app/GLM-5.3`](https://github.com/GLM-5-3-app/GLM-5.3) repository, specifically extracted for **Promptsmith** to enrich its prompt-engineering rubrics, reasoning model guidelines, harness notes, repo-rules, and coding-agent briefs.

---

## 1. Scraped Sources Overview

| Source / Repository | Path in `scrapes/` | Files | Primary Value for Promptsmith |
| :--- | :--- | :---: | :--- |
| **[`Z.ai GLM-5.3 Documentation`](https://docs.z.ai/guides/llm/glm-5.3)** | [`scrapes/glm/docs/`](scrapes/glm/docs/) | 9 | Official model specification, always-on reasoning dynamics, 1M context / 128K generation ceiling, dual protocol endpoints (`/coding/paas/v4`, `/v1`, `/anthropic`), streaming delta contracts (`reasoning_content`), automatic context caching, and Coding Agent Best Practice framework (Goal, Context, Constraints, Done-When). |
| **[`GLM-5.3 Client & Weights Hub`](https://github.com/GLM-5-3-app/GLM-5.3)** | [`scrapes/glm/client-hub/`](scrapes/glm/client-hub/) | 6 | Standalone desktop client architecture, local project library context management, token efficiency benchmarks (50,000 tokens/task vs Opus 120,000 tokens/task), and drop-in configurations for Claude Code, Cursor, and Cline. |

---

## 2. Core Prompting Intelligence for Promptsmith

### A. Always-On Reasoning Dynamics & Effort Levers

#### 1. Mandatory Reasoning Architecture (`thinking: {type: "enabled"}`)
- **The Core Constraint:**
  Unlike earlier generations (GLM-5.2/5.1/4.5) where thinking could be toggled off via `thinking: {type: "disabled"}`, **GLM-5.3 and GLM-5.3-Flash operate with mandatory, always-on reasoning**.
- **Error Behavior:**
  Passing `thinking.type: "disabled"` in an API call returns a validation error and fails the request immediately.
- **Migration & Neutralization Rule:**
  When adapting workflows from non-reasoning models or legacy GLM checkpoints, the harness must set `thinking: {type: "enabled"}` and calibrate intensity using `reasoning_effort` rather than attempting to disable thinking.

#### 2. Three-Tier Reasoning Effort Calibration
GLM-5.3 supports three distinct reasoning effort tiers:

| Parameter Value | Tier Name | Semantic Scope | Recommended Promptsmith Use Case |
| :--- | :--- | :--- | :--- |
| `low` | Lightweight Reasoning | Rapid code modifications, single-file lint fixes, trivial docstring updates | Quick edits, commit message synthesis, simple schema migrations |
| `high` | Enhanced Reasoning | Multi-file feature additions, algorithmic refactors, test authoring | Standard coding agent briefs, cross-component refactors |
| `max` *(Default)* | Deep Reasoning | Long-horizon debugging, architectural design, complex agentic autonomy | Multi-hour autonomous sessions, root-cause forensics, system design |

#### 3. Outer Harness Translation & Fallback Handling
In third-party coding agent harnesses, reasoning controls map dynamically into Z.ai's schema:
- **Claude Code:** Translates `/effort` levels into `thinking.type` and `output_config.effort`. Settings of `minimal`, `light`, or `low` map to `low`; `medium` or `high` map to `high`; `xhigh`, `max`, or `ultra` map to `max`. If a user disables thinking in Claude Code, the Z.ai proxy intercepts the request and automatically sets `reasoning_effort="low"` with thinking enabled rather than throwing an error.
- **OpenAI Codex:** Uses `reasoning.effort` directly (`low`, `high`, `max`).
- **Processing Priority:** Explicit `reasoning_effort` flag > thinking toggle > default `max`.

#### 4. Sampling Temperature Calibration ($T=1.0$)
- **Official Specification:** Recommended `temperature = 1.0` for reasoning generation under the Z.ai API.
- **The Rationale:**
  Like other reinforcement-learning reasoning models trained via test-time search (SAO / GRPO), GLM-5.3 requires sufficient stochastic sampling to explore branching search spaces. Setting `temperature = 0.0` or forcing greedy decoding risks repetitive self-referential loops during deep thinking phases.

---

### B. Dual Protocol Architecture & Drop-In Harness Endpoints

#### 1. Universal Protocol Multiplexing
Z.ai provides native dual-protocol support, enabling GLM-5.3 to act as a drop-in replacement across tools without requiring prompt dialect translation:

| Protocol | Base URL / Endpoint | Target Tool / Integration |
| :--- | :--- | :--- |
| **OpenAI Chat Completion** | `https://api.z.ai/api/coding/paas/v4` | Cline, Roo-Cline, Cursor, Continue, Aider, OpenCode |
| **OpenAI Response Protocol** | `https://api.z.ai/api/v1` | OpenAI Python/Node SDK, LiteLLM, Codex |
| **Anthropic Message Protocol** | `https://api.z.ai/api/anthropic` | Claude Code, Goose, Anthropic SDK wrappers |

#### 2. Claude Code Drop-In Configuration
To run GLM-5.3 or GLM-5.3-Flash inside Claude Code, configure `~/.claude/settings.json`:
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "ANTHROPIC_API_KEY": "your-z-ai-api-key",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1000000",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-5.3-flash[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5.3[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5.3[1m]"
  }
}
```
The `[1m]` suffix explicitly requests the 1,000,000-token context window, while `CLAUDE_CODE_AUTO_COMPACT_WINDOW: "1000000"` ensures Claude Code's auto-compactor does not prematurely truncate long codebase sessions.

#### 3. Cline & Cursor Drop-In Configuration
In Cline or Cursor's OpenAI-compatible settings:
- **Base URL:** `https://api.z.ai/api/coding/paas/v4`
- **Model ID:** `glm-5.3` (text-only) or `glm-5.3-flash` (multimodal visual coding)
- **Context Window:** `1000000`
- **Max Output Tokens:** `128000` (or `4096`–`16384` per agent turn)

---

### C. Token Economics, Efficiency & Benchmark Profile

#### 1. Context Envelope & Generation Limits
- **Input Context Window:** 1,000,000 tokens (1M tokens). Enables hydrating full enterprise repositories, dependency graphs, and documentation sets in memory.
- **Maximum Output Ceiling:** 128,000 tokens (128K tokens). Supports generating complete multi-module implementations or full test suites in a single generation.

#### 2. Efficiency vs Claude Opus 4.8 on Z.ai Code Bench
On Z.ai Code Bench (High tier), evaluating real-world developer scenarios with end-to-end task completion and checklist accuracy:
- **Claude Opus 4.8:** 29.5% accuracy, consuming **~120,000 tokens** per task.
- **GLM-5.3 (High Effort):** 31.4% accuracy, consuming **~50,000 tokens** per task.
- **GLM-5.3 (Max Effort):** 34.5% accuracy, consuming **~75,000 tokens** per task.
- **Takeaway for Promptsmith:** GLM-5.3 achieves higher solve rates while using less than half the tokens per task compared to closed frontier models, dramatically reducing the session context tax in multi-turn coding loops.

#### 3. Post-Training Scaling Architecture
GLM-5.3 shares the same 743B base model as GLM-5.2. All performance gains stem from scalable post-training:
- **SAO RL with Compaction:** Step-level Advantage Optimization with trace compaction, preventing catastrophic forgetting and maintaining reasoning fidelity across long horizons.
- **Slime Framework & Verifiable Environments:** Synthetic environment generation where research agents build runnable environments with hidden state, verified by judge agents using binary reward signals (oracle, no-op, and unsolved-state checks).
- **Public Benchmark Jumps:**
  - Terminal-Bench 3.0: 4.6 $\rightarrow$ **28.3** (#1 open-weights model).
  - DeepSWE v1.1: 46.2 $\rightarrow$ **66.9**.
  - SWE-Marathon: 19.4 $\rightarrow$ **42.5**.
  - Agents' Last Exam (CLI): 23.8 $\rightarrow$ **28.5**.

#### 4. The Flash MoE Variant (`glm-5.3-flash`)
- **Parameters:** 320B total parameters with 18B active tokens per step.
- **Attention Architecture:** Hybrid sparse and linear attention, cutting attention compute by 3.01x and KV cache by 4.44x versus standard dense attention.
- **Multimodal Visual Coding:** Native image, video, and text inputs for UI inspection, screenshot debugging, and GUI automation.
- **Quota Advantage:** 3x token points multiplier on GLM Coding Plans.

#### 5. Automatic Context Caching & Off-Peak Dynamics
- **Implicit Cache Identification:** The API automatically hashes and caches repeated system prompts and conversation prefixes without requiring explicit cache control markers.
- **Billing Transparency:** Cached tokens are reported in `usage.prompt_tokens_details.cached_tokens` at discounted rates.
- **Off-Peak Economy:** Model invocations during weekends and off-peak hours consume only 50% points on Coding Plans.

---

### D. Prompt Construction Patterns for Coding Agents

#### 1. Alignment with Z.ai's 4-Element Task Framework
Official Z.ai coding agent guidance (`scrapes/glm/docs/best-practice.md`) formalizes four structural elements for agent tasks, which align directly with Promptsmith's 7-pillar rubric:

```
┌────────────────────────────────────────────────────────┐
│ 1. Goal: Explicit declaration of what to build/fix     │
│ 2. Context: Files, symbols, error traces, invariants   │
│ 3. Constraints: Boundaries, conventions, anti-patterns │
│ 4. Done When: Executable tests, observable outcomes    │
└────────────────────────────────────────────────────────┘
```

#### 2. Zero-Shot Problem Framing & Anti-CoT Scaffolds
- **Do Not Micromanage Deliberation:** Never prompt GLM-5.3 with `"Think step by step"`, `"Deliberate carefully"`, or `<thinking>` pseudotags. Test-time reasoning is intrinsic to the model's post-trained weights.
- **Zero-Shot Problem Specification:** Present the task directly in a clean zero-shot format. Provide necessary architectural context, then state the core directive without conversational filler.

#### 3. Tail-Placed Output Format Contracts
- Like DeepSeek and modern frontier models, GLM-5.3 demonstrates peak instruction adherence when output format contracts are placed at the very end of the prompt envelope.
- **Diff-First Contract:** Mandate unified diffs or minimal targeted replacement chunks to prevent full-file echoing and preserve context bandwidth.

#### 4. Plan-First Autonomy for Complex Tasks
For multi-step or cross-module tasks:
1. Direct the model to produce an explicit implementation plan before modifying files.
2. Confirm the plan or allow the agent to self-verify before transitioning into code execution.
3. Separate temporary prompt instructions from long-lived repository rules stored in `CLAUDE.md`, `GEMINI.md`, or `AGENTS.md`.

---

### E. Streaming Delta Contracts (`reasoning_content` vs `content`)

#### 1. Server-Sent Events (SSE) Stream Structure
When streaming responses (`stream=True`), GLM-5.3 emits incremental deltas across two dedicated fields:

```
event: message
data: {"choices": [{"delta": {"reasoning_content": "Analyzing file dependencies..."}}]}

event: message
data: {"choices": [{"delta": {"content": "```python\ndef handler():\n..."}}]}
```

- **`delta.reasoning_content`:** Contains real-time reasoning tokens from the model's internal deliberation trace.
- **`delta.content`:** Contains the final, user-facing output or executable code blocks.
- **`finish_reason` & `usage`:** Emitted only in the terminating chunk.

#### 2. Critical Harness Handling Rules
1. **Never Mix Deliberation into Tool Calls:** Harnesses must isolate `reasoning_content` from tool-call argument buffers. Feeding reasoning tokens into JSON parameter parsers causes parsing failures.
2. **UI Segregation:** Display `reasoning_content` in collapsible thinking disclosure boxes or silent background logs, keeping the primary terminal clear for executable diffs and tool logs.
3. **Usage Tracking:** Extract `prompt_tokens_details.cached_tokens` from the terminal chunk to accurately monitor session token burn and caching efficiency.

---

## 3. Actionable Recommendations for Promptsmith

### Recommendation 1: Update `references/harness-notes.md`
Add a dedicated section for GLM-5.3 detailing:
- Z.ai GLM Coding Plan and dual-protocol endpoints (`/coding/paas/v4`, `/v1`, `/anthropic`).
- Mandatory always-on reasoning (`thinking: {type: "enabled"}`) and effort mapping (`low`, `high`, `max`).
- Sampling temperature ($T=1.0$) for reasoning exploration.
- 1M context configuration (`[1m]` suffix and `CLAUDE_CODE_AUTO_COMPACT_WINDOW: 1000000`).
- Token efficiency metrics (50k tokens/task vs Opus 120k).

### Recommendation 2: Update `references/best-practices.md`
Add GLM-5.3 to Section 8 (Harness Summary Cheatsheet):
- Document GLM-5.3 configuration parameters, effort tiers, and protocol URLs.
- Highlight Z.ai's 4-Element Task Framework (Goal, Context, Constraints, Done When).

### Recommendation 3: Extend Tooling in `tools/token_audit.py` & `tools/eval_rubrics.py`
- Update `generate_prompt()` in `tools/token_audit.py` to recognize GLM models (e.g. `glm`, `glm-5.3`, `glm-5.3-flash`) and set appropriate frontmatter and constraints.
- Update `tools/eval_rubrics.py` with a regression assertion validating GLM-5.3 prompt generation and rubric compliance.
