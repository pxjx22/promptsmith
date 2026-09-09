# OpenAI Scraping & Prompt Intelligence Reference

This directory contains scraped reference material from the [`openai`](https://github.com/openai) GitHub organization, specifically extracted for **Promptsmith** to enrich its prompt-engineering rubrics, harness notes, repo-rules, and coding-agent briefs.

---

## 1. Scraped Repositories Overview

| Repository | Path in `scrapes/` | Files | Primary Value for Promptsmith |
|---|---|---|---|
| **[`openai-cookbook`](https://github.com/openai/openai-cookbook)** | [`scrapes/openai/cookbook/`](scrapes/openai/cookbook/) | 163 | Prompt engineering guides (`examples/`), reasoning model patterns (`examples/o-series/`, `examples/o1/`), ExecPlans for autonomous coding (`articles/codex_exec_plans.md`), Harmony role hierarchy (`articles/openai-harmony.md`), prompt caching benchmarks (`examples/Prompt_Caching_201.ipynb`), and agent recipes. |
| **[`evals`](https://github.com/openai/evals)** | [`scrapes/openai/evals/`](scrapes/openai/evals/) | 964 | Model-based evaluation rubrics (`evals/registry/modelgraded/`), `cot_classify` scoring engine (`evals/elsuite/modelgraded/classify_utils.py`), completion function protocols (`docs/completion-fn-protocol.md`), and evaluation harness architectures. |
| **[`swarm`](https://github.com/openai/swarm)** | [`scrapes/openai/swarm/`](scrapes/openai/swarm/) | 243 | Multi-agent orchestration loop (`swarm/core.py`), agent definition types (`swarm/types.py`), routine handoff patterns via tool return (`examples/airline/`), and stateless context variable management. |
| **[`openai-python`](https://github.com/openai/openai-python)** | [`scrapes/openai/openai-python/`](scrapes/openai/openai-python/) | 129 | Developer role message specifications (`src/openai/types/chat/chat_completion_developer_message_param.py`), strict JSON schema generation (`src/openai/lib/_pydantic.py`), `.parse()` parsing helpers (`docs/helpers.md`), and reasoning configuration models (`src/openai/types/shared_params/reasoning.py`). |

---

## 2. Core Prompting Intelligence for Promptsmith

### A. System Prompt Design & Developer Role Conventions
- **Harmony Role & Instruction Hierarchy** ([`articles/openai-harmony.md`](scrapes/openai/cookbook/articles/openai-harmony.md)):
  OpenAI's modern architecture enforces a strict priority order: `system` > `developer` > `user` > `assistant` > `tool`.
  - **`system` Role:** Reserved for infrastructure-level configuration (knowledge cutoff date, reasoning effort limits, native tool capability flags).
  - **`developer` Role:** The primary instruction channel for agent behaviors, constraints, and operational guidelines. In models starting from `o1`, `developer` messages replace informal `system` prompts ([`chat_completion_developer_message_param.py`](scrapes/openai/openai-python/src/openai/types/chat/chat_completion_developer_message_param.py)). They possess higher steering weight than user messages and are resistant to prompt injection.
- **ExecPlans as Living Documents** ([`articles/codex_exec_plans.md`](scrapes/openai/cookbook/articles/codex_exec_plans.md)):
  For autonomous coding over long horizons (7+ hours), agents stay on track by referencing an ExecPlan (`PLANS.md`) in `AGENTS.md`. Key design requirements:
  - Completely self-contained: Written so an engineer with zero codebase context can execute each step.
  - Documents design choices, verification commands, and state checkpoints.
  - Mandates autonomous progression through milestones without stopping to ask "what next?".
- **Delimited Data Envelopes** ([`docs/build-eval.md`](scrapes/openai/evals/docs/build-eval.md)):
  Isolate inputs and candidate completions using explicit block delimiters (`[BEGIN DATA] ... [END DATA]` or XML tags `<context>`, `<instructions>`). This prevents untrusted text from bleeding across instruction boundaries.

### B. Reasoning Model Prompting Rules (`o1`, `o3`, `gpt-5+` Series)
- **CoT Damping & Anti-"Think Step-by-Step"** ([`examples/o-series/o3o4-mini_prompting_guide.ipynb`](scrapes/openai/cookbook/examples/o-series/o3o4-mini_prompting_guide.ipynb)):
  Reasoning models have native test-time compute. Prompts must **never** include "think step by step", "show your inner chain of thought", or instructions micromanaging the intermediate reasoning trajectory. Adding external CoT pressure creates conflicting deliberation loops and degrades performance.
- **Direct, Minimalist Prompting**:
  Prompts should state the problem clearly, provide necessary context/evidence, specify hard constraints, and state explicit verification criteria. Let the model spend its reasoning tokens exploring hypotheses rather than parsing prompt bloat.
- **Front-Load Constraints in Tool Descriptions**:
  Place negative constraints, formatting rules, and escaping conventions at the very beginning of tool parameter descriptions. In OpenAI benchmarks, front-loading boosted tool calling accuracy by +6%.
- **Anti-Laziness & Premature Promise Directives**:
  Reasoning models can occasionally promise future action or assert that work is happening in the background. Use the explicit negative rule:
  > *"Do NOT promise to call a function later. If a function call is required, emit it now; otherwise respond normally."*
- **Flat Schemas over Deeply Nested Objects**:
  Keep tool schemas flat (<20 arguments, shallow nesting). Deeply nested object hierarchies increase the probability of omitted required fields.
- **Reasoning Parameter Tuning** ([`reasoning.py`](scrapes/openai/openai-python/src/openai/types/shared_params/reasoning.py)):
  - `reasoning_effort`: `Literal["none", "minimal", "low", "medium", "high", "xhigh", "max"]`. Use `"low"` or `"minimal"` for routine feature edits and bugfixes to avoid deliberation plateaus; escalate to `"high"` only for difficult architectural puzzles.
  - `context`: `"auto" | "current_turn" | "all_turns"`. In multi-turn reasoning agents, passing reasoning items across turns (`all_turns`, default in GPT-5.6) prevents reasoning amnesia.

### C. Structured Outputs & JSON Schema Compliance Patterns
- **Constrained Decoding via `strict: true`** ([`examples/Structured_Outputs_Intro.ipynb`](scrapes/openai/cookbook/examples/Structured_Outputs_Intro.ipynb), [`docs/helpers.md`](scrapes/openai/openai-python/docs/helpers.md)):
  When `response_format` or tool definitions set `strict: true`, OpenAI models use grammar-constrained sampling, guaranteeing 100% adherence to the supplied JSON schema.
- **Strict Schema Requirements** ([`_pydantic.py`](scrapes/openai/openai-python/src/openai/lib/_pydantic.py)):
  1. Every object schema must explicitly declare `"additionalProperties": False`.
  2. Every key in `"properties"` must be explicitly included in `"required"`.
  3. No naked `$ref` overrides with peer fields; schemas must be unrolled.
- **Two-Stage Chaining for Unsupported Models** ([`examples/o1/Using_chained_calls_for_o1_structured_outputs.ipynb`](scrapes/openai/cookbook/examples/o1/Using_chained_calls_for_o1_structured_outputs.ipynb)):
  When using models without native structured output support, chain two steps: Step 1 uses the reasoning model for deep unstructured analysis -> Step 2 passes the text to a fast model (e.g., GPT-4o-mini) with `strict: true` to format into schema deterministically.

### D. Multi-Agent Orchestration: Swarm Handoffs & Routines
- **The Routine Pattern** ([`swarm/core.py`](scrapes/openai/swarm/swarm/core.py), [`examples/airline/`](scrapes/openai/swarm/examples/airline/)):
  Instead of one bloated agent prompt attempting to handle all capabilities, tasks are split into isolated "routines" (e.g., Triage, Modification, Verification). Each routine has its own focused agent prompt and minimal toolset.
- **Handoffs via Tool Return Value** ([`swarm/core.py#L71-L88`](scrapes/openai/swarm/swarm/core.py)):
  Swarm introduces a clean idiom for agent handoffs: a tool simply returns an `Agent` instance:
  ```python
  def transfer_to_database_specialist():
      return database_agent
  ```
  The orchestration loop detects the returned `Agent`, appends the tool result to history, switches `active_agent = result.agent`, and executes the subsequent turn under the new agent's developer prompt and tool schema.
- **Dynamic System Prompts**:
  Agent `instructions` can be a callable function accepting `context_variables`. The system prompt is dynamically evaluated immediately prior to inference, injecting runtime parameters cleanly.
- **Schema Stripping of Context Variables**:
  Context variables (user profile, auth tokens, session state) are kept in orchestrator state. Swarm automatically strips `context_variables` from the tool parameters sent to the LLM and injects the dictionary directly into the local Python function call at execution time.

### E. Evaluation Intelligence & Model-Based Grading Rubrics (`evals`)
- **`cot_classify` as the Gold Standard** ([`evals/elsuite/modelgraded/classify_utils.py`](scrapes/openai/evals/evals/elsuite/modelgraded/classify_utils.py)):
  Direct classification (`classify`) suffers from immediate-token bias, while explanation-after-choice (`classify_cot`) fails to leverage reasoning for the decision token. The gold standard pattern is `cot_classify`:
  ```
  First, write out in a step by step manner your reasoning to be sure that your conclusion is correct.
  Avoid simply stating the correct answer at the outset.
  Then print only a single choice from {choices} (without quotes or punctuation) on its own line corresponding to the correct answer.
  At the end, repeat just the answer by itself on a new line.

  Reasoning:
  ```
- **Reverse-Line Parsing Engine**:
  To robustly parse decisions from verbose reasoning text, evaluate lines in reverse order (`lines[::-1]`) against allowed choice strings.
- **Rubric Taxonomies in Practice**:
  - *Set-Theoretic Rubric* ([`fact.yaml`](scrapes/openai/evals/evals/registry/modelgraded/fact.yaml)): Grades factual consistency as Subset ($\subseteq$), Superset ($\supseteq$), Same ($=$), Conflict ($\neq$), or Inconsequential Difference ($\approx$).
  - *Parametric Criteria Checking* ([`closedqa.yaml`](scrapes/openai/evals/evals/registry/modelgraded/closedqa.yaml)): Dynamic criteria injection for correctness, relevance, or conciseness.
  - *Additive Checklist Rubric*: Sums individual boolean validation points into a composite scalar score.
- **Solver vs SolverEval Decoupling** ([`docs/build-eval.md`](scrapes/openai/evals/docs/build-eval.md)):
  Strictly decouple the task/environment specification (`SolverEval`) from the agent/prompt scaffolding (`Solver`), cloning the solver per sample to guarantee state isolation.

### F. Prompt Caching & Context Architecture
- **Prefix Invariance & Static Root Alignment** ([`examples/Prompt_Caching101.ipynb`](scrapes/openai/cookbook/examples/Prompt_Caching101.ipynb)):
  Place static instructions, developer prompts, and schema definitions at the very beginning of the context. Variable inputs, user messages, and dynamic variables must sit at the end. Minimum threshold for KV caching is 1,024 tokens.
- **`prompt_cache_key` as Routing Shard Key** ([`examples/Prompt_Caching_201.ipynb`](scrapes/openai/cookbook/examples/Prompt_Caching_201.ipynb)):
  Using a shared `prompt_cache_key` routes requests to the same GPU host, yielding up to an 8.5% increase in cache hit rate and a 23% reduction in input token cost (~15 RPM sweet spot per server).
- **Batch Compaction vs Rolling Cache Invalidation**:
  Sliding-window eviction that drops one message per turn shifts the conversation prefix every step, invalidating 100% of the KV cache. Instead, use discrete batch truncation (e.g. `retention_ratio: 0.7` or compaction threshold), which evicts the oldest 30% in one chunk, keeping 70% of the KV cache intact for subsequent turns.

---

## 3. Actionable Recommendations for Promptsmith

### Recommendation 1: Update `references/best-practices.md`
1. **Section 1 (Clarity & Framing):** Add the **OpenAI Harmony instruction hierarchy** (`system` > `developer` > `user` > `assistant` > `tool`) and establish `developer` messages as the primary steering role for modern OpenAI models.
2. **Section 3 (Reasoning & Thinking):** Add **Anti-CoT guidelines for reasoning models** (bar "think step by step" and explicit thought scripting for o1/o3/GPT-5+; front-load negative constraints in tool descriptions).
3. **Section 9 (Token Efficiency & Context Architecture):** Document **Batch Compaction vs Rolling Invalidation** (`retention_ratio: 0.7`) and **Shard-Key Routing** (`prompt_cache_key`).
4. **New Section: Evaluation & Model-Based Grading:** Add the **`cot_classify` pattern** (deliberation first, answer on separate line, reverse-line parsing) and the **Set-Theoretic evaluation taxonomy**.

#### Proposed Patch for `references/best-practices.md`
```diff
--- a/references/best-practices.md
+++ b/references/best-practices.md
@@ -34,6 +34,13 @@
 - Standard tags: `<role>`, `<context>`, `<document>`, `<instructions>`, `<examples>`, `<output_format>`.
 
+**Instruction Hierarchy & Role Precedence (OpenAI Harmony):**
+Why: Modern reasoning models enforce explicit priority: `system` > `developer` > `user` > `assistant` > `tool`.
+- Use `developer` messages for authoritative behavioral contracts, repo rules, and tool descriptions.
+- In reasoning models (o1/o3/GPT-5+), developer instructions supersede conflicting user turns and resist injection.
+
 ---
 
 ## 2. Long Context, Grounding & Prompt Caching
@@ -74,6 +81,14 @@
 
 ## 3. Reasoning, Thinking & Abstraction
 
+**CoT Damping on Native Reasoning Models (o1, o3, GPT-5+):**
+Why: Models with native test-time compute already deliberate internally.
+- Weak: `Think step by step and explain your reasoning before taking any action.`
+- Strong: `Solve the problem directly. Comply with all stated constraints and run tests to verify.`
+- Rule: Never prompt native reasoning models with manual chain-of-thought phrases ("think step by step").
+- Tool constraints: Front-load escaping rules and negative boundaries at the top of tool parameter descriptions.
+
+**Anti-Laziness Directives:**
+- Include: `Do NOT promise to call a function later. If a function call is required, emit it now; otherwise respond normally.`
+
 ---
 
 ## 9. Token Efficiency & Context Architecture (2026 Research)
@@ -192,6 +207,12 @@
 - Keep system instructions, repository rules, and static schema definitions byte-for-byte identical at the prompt root.
 - Place variable inputs (`{{INPUT}}`) after the static prefix.
 
+**Batch Compaction over Rolling Invalidation:**
+Why: Dropping messages one turn at a time shifts the start offset of the context, destroying 100% of the KV cache every turn.
+- Strategy: Use discrete batch compaction (`retention_ratio: 0.7` or threshold-based pruning) to drop the oldest 30% in one chunk, keeping 70% of the cache intact for the next N turns.
+- Routing Locality: Use `prompt_cache_key` to route requests to the same GPU host (~15 RPM per prefix).
+
```

---

### Recommendation 2: Update `references/harness-notes.md` (Codex Section)
1. Specify `developer` role over `system` role for Codex and GPT-5/6 prompts.
2. Add ExecPlan (`PLANS.md`) conventions for multi-hour autonomous execution.
3. Detail `reasoning_effort` selection (`"low"` for routine edits, `"medium"`/`"high"` for complex architectures) and `reasoning.context = "all_turns"` retention.
4. Add batch compaction to protect the 30-minute prompt cache.

#### Proposed Patch for `references/harness-notes.md`
```diff
--- a/references/harness-notes.md
+++ b/references/harness-notes.md
@@ -78,6 +78,9 @@
 - **Autonomy posture:** Optimized for deep, multi-hour autonomous execution. Set the stance: "Act as an autonomous senior engineer — proactively gather context, plan, implement, test, and refine without waiting for additional prompts at each step. Bias to action; make reasonable assumptions; only stop with questions if truly blocked. Every turn ends with a concrete edit or an explicit blocker."
+- **Role conventions:** Use `role: "developer"` for system-level instructions and tool guidance rather than legacy `system` role. Developer messages carry primary steering authority in GPT-6/5.6.
+- **ExecPlans (PLANS.md):** For tasks spanning multiple steps, write an ExecPlan living document. Must be self-contained, record all decisions, and advance through milestones autonomously without pausing to query the user.
 - **Prompt Cache Breakpoint & 30m TTL:** Codex uses a 30-minute sliding window with 50% discount on cached tokens. Ensure `prompt_cache_breakpoint = true` in config to prevent volatile tool outputs from invalidating the system prompt.
+- **Batch Compaction:** Avoid rolling turn-by-turn truncation. When context window approaches limits, prune in 30% chunks (`retention_ratio: 0.7`) to maintain 70% KV cache validity across turns.
 - **Reasoning Effort Tuning:** In `~/.codex/config.toml`, set `reasoning_effort = "low"` for routine feature edits and bugfixes to avoid test-time deliberation plateaus; escalate to `"medium"`/`"high"` only for deep architectural forensics.
+- **Reasoning Context:** Set `reasoning.context: "all_turns"` to preserve reasoning tokens across tool interactions and prevent multi-turn amnesia.
 - **Patching over rewriting:** Strict solver tool priority (`rg` over grep, `apply_patch` for single-file edits, dedicated `git` tool over raw shell). Bar full-file rewrites.
```

---

### Recommendation 3: Update `references/repo-rules.md`
1. Include `developer` message role distinction in the Tool Discovery Matrix for Codex/OpenAI.
2. Note ExecPlan (`PLANS.md`) integration alongside `AGENTS.md`.
