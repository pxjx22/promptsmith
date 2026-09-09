# DeepSeek Scraping & Prompt Intelligence Reference

This directory contains scraped and curated reference material from the [`deepseek-ai`](https://github.com/deepseek-ai) GitHub organization and official technical reports, specifically extracted for **Promptsmith** to enrich its prompt-engineering rubrics, reasoning model guidelines, harness notes, repo-rules, and coding-agent briefs.

---

## 1. Scraped Repositories Overview

| Source / Repository | Path in `scrapes/` | Files | Primary Value for Promptsmith |
| :--- | :--- | :---: | :--- |
| **[`DeepSeek-R1`](https://github.com/deepseek-ai/DeepSeek-R1)** | [`scrapes/deepseek/r1/`](scrapes/deepseek/r1/) | 5 | Reasoning model technical report, reinforcement learning (GRPO) dynamics, zero-shot emergence, few-shot degradation warnings, temperature/sampling guidelines (`0.6`), `<think>\n` prefill trigger, and official web/file prompt templates. |
| **[`DeepSeek-V3`](https://github.com/deepseek-ai/DeepSeek-V3)** | [`scrapes/deepseek/v3/`](scrapes/deepseek/v3/) | 20 | Architecture specifications, Multi-Head Latent Attention (MLA), Multi-Token Prediction (MTP), distributed inference engine (`inference/generate.py`), FP8 GEMM kernels, and R1 distillation with reflective system prompts. |
| **[`DeepSeek-Coder-V2`](https://github.com/deepseek-ai/DeepSeek-Coder-V2)** | [`scrapes/deepseek/coder-v2/`](scrapes/deepseek/coder-v2/) | 6 | Code intelligence, 338 supported languages, Fill-In-The-Middle (FIM) prompt formatting (`<｜fim begin｜>`, `<｜fim hole｜>`, `<｜fim end｜>`), chat template syntax, and the critical trailing space anomaly fix on `Assistant:`. |
| **[`DeepSeek-Math`](https://github.com/deepseek-ai/DeepSeek-Math)** | [`scrapes/deepseek/math/`](scrapes/deepseek/math/) | 42 | Mathematical reasoning evaluation suites, few-shot CoT and PAL prompt libraries (`evaluation/few_shot_prompts/`), Tool-Integrated Reasoning (TIR) runtime harness (`infer/run_tool_integrated_eval.py`), and stop token conventions. |
| **[`awesome-deepseek-integration`](https://github.com/deepseek-ai/awesome-deepseek-integration)** | [`scrapes/deepseek/awesome-integration/`](scrapes/deepseek/awesome-integration/) | 149 | 70+ client/IDE/agent integration guides and schemas (Cline, Roo-Cline, Cursor, Continue, Avante.nvim, Model Context Protocol MCP server). |
| **Research Papers Archive** | [`scrapes/deepseek/papers/`](scrapes/deepseek/papers/) | 8 | Plaintext extractions and curated technical notes for arXiv:2501.12948 (R1), arXiv:2412.19437 (V3), arXiv:2406.11931 (Coder-V2), and arXiv:2402.03300 (Math). |

---

## 2. Core Prompting Intelligence for Promptsmith

### A. Reasoning Model Prompting Rules (DeepSeek-R1 Series)

#### 1. Zero-Shot Emergence & Why Few-Shot Prompting Degrades Reasoning
- **The Finding (R1 Technical Report, Section 5.2):**
  > *"When evaluating DeepSeek-R1, we observe that it is sensitive to prompts. Few-shot prompting consistently degrades its performance. Therefore, we recommend users directly describe the problem and specify the output format using a zero-shot setting for optimal results."*
- **The Mechanism:**
  DeepSeek-R1 relies on large-scale test-time search incentivized by Group Relative Policy Optimization (GRPO). When provided with few-shot exemplars containing human-written chains of thought, the model suffers from **premature hypothesis pruning** and **shortcut bias**. The exemplar tokens act as strong attention anchors, biasing the policy away from exploring alternative reasoning branches and degrading solve rates on complex math, logic, and code benchmarks. Standard benchmarks like MMLU-Pro, C-Eval, and CLUE-WSC had to be modified to zero-shot because few-shot prompts systematically hurt R1 performance.
- **Rule for Promptsmith:**
  For DeepSeek-R1 (and `deepseek-reasoner`), **never provide few-shot CoT exemplars**. Present the task as a clean, direct zero-shot problem statement.

#### 2. Anti-CoT Forcing (No Manual Thought Scripting)
- Do not instruct DeepSeek-R1 with phrases like `"Think step by step"`, `"Show your work in detail"`, or `"Deliberate carefully before answering"`. The model has native test-time compute; prompt instructions attempting to micromanage the deliberation structure conflict with the learned GRPO policy.
- Instead, specify hard requirements, operational constraints, and verification criteria.

#### 3. Output Format Directives at the Prompt Tail
- DeepSeek models are sensitive to instruction positioning. Format constraints must sit at the very end of the user turn:
  - Math/deterministic problems: `"Please reason step by step, and put your final answer within \\boxed{}."`
  - Code problems: `"Format your response with the final executable code block enclosed in \`\`\`language ... \`\`\`."`

#### 4. The Sampling Temperature Sweet Spot (0.6) & The Greedy Decoding Failure Mode
- **Recommended Range:** `temperature = 0.5 - 0.7` (Official default: **`0.6`**, `top_p = 0.95`).
- **The Greedy Decoding Trap:**
  In traditional instruction LLMs, deterministic tasks (code generation, mathematical calculation, schema extraction) mandate `temperature = 0.0` to ensure reproducibility.
  In RL-trained reasoning models like DeepSeek-R1, setting `temperature = 0.0` or using greedy decoding creates severe degeneration: **endless token repetition**, circular reasoning loops, and early reasoning truncation. Stochastic sampling is mathematically necessary for the policy to navigate around low-entropy dead ends during test-time search.

#### 5. The `<think>\n` Prefix Prefill Trigger (Thinking Bypass Fix)
- **Observed Failure Mode:** On certain simple queries, direct instructions, or short dialogue turns, DeepSeek-R1 occasionally bypasses its internal reasoning loop entirely, emitting `<think>\n\n</think>` with zero tokens of deliberation and answering poorly.
- **Harness Remediation:**
  In agent harnesses supporting output prefilling (or local servers like SGLang/vLLM), pre-fill the assistant response with `<think>\n`. This forces the generation decoder into thinking mode, guaranteeing thorough reflection before the model emits `</think>`.

#### 6. The Zero System Prompt Contract
- DeepSeek's official web/app interface and API documentation explicitly advise:
  > *"Avoid adding a system prompt; all instructions should be contained within the user prompt."*
- When using `deepseek-reasoner` (R1), system role messages can lead to erratic reasoning depth or degraded instruction following. All persona guidelines, tool definitions, and task constraints should be bundled directly into the user message envelope.

---

### B. Code Generation & Fill-In-The-Middle (FIM) Patterns (DeepSeek-Coder-V2)

#### 1. Special FIM Tokens
DeepSeek-Coder-V2 uses dedicated boundary markers:
- `<｜fim begin｜>`: Marks the start of the prefix context.
- `<｜fim hole｜>`: Marks the insertion point (the hole to fill).
- `<｜fim end｜>`: Marks the start of the suffix context.

#### 2. Production FIM Template (PSM Permutation)
```
<｜fim begin｜>{code_prefix}<｜fim hole｜>{code_suffix}<｜fim end｜>
```
The model generates tokens to fill the `{code_suffix}` gap, terminating on `<｜end of sentence｜>`.

#### 3. The Trailing Space Anomaly on `Assistant:`
- **CRITICAL WARNING (Documented in official repo issue #12):**
  When formatting chat templates for DeepSeek-Coder-V2 (and DeepSeek-V3/R1 tokenizers), the generation prompt ends with:
  ```
  Assistant:
  ```
  **Never append a trailing space after `Assistant:`** (`Assistant: `).
- **Failure Mode on 16B-Lite and MoE Checkpoints:**
  Adding a space after `Assistant:` corrupts token boundary alignment, causing:
  1. Language switching: English prompts receiving responses in Chinese.
  2. Unicode garbage characters.
  3. Infinite repetitive looping.
- **Remediation for Promptsmith:** Always ensure prompts and template generators strip trailing whitespace from role labels.

#### 4. Repository Context Hydration
- DeepSeek-Coder-V2 supports 128K context across 338 programming languages.
- When hydrating multi-file repositories, DeepSeek's evaluation harnesses structure files using explicit, unambiguous envelopes:
  ```
  [file name]: {relative_path}
  [file content begin]
  {file_content}
  [file content end]
  ```
- This envelope cleanly separates file metadata from source syntax and prevents code blocks from prematurely closing prompt wrappers.

---

### C. System Prompt Design & Special Token Conventions (DeepSeek-V3)

#### 1. Conversation Role Markers & Grammar
DeepSeek models use special delimited tokens with full-width pipe characters (`｜`):
- `<｜begin of sentence｜>`: BOS token (automatically added by tokenizer when `add_special_tokens=True`).
- `<｜User｜>`: Delimits user turns.
- `<｜Assistant｜>`: Delimits assistant responses.
- `<｜end of sentence｜>`: EOS token.

Standard Turn Layout:
```
<｜begin of sentence｜><｜User｜>{user_message}<｜Assistant｜>{assistant_message}<｜end of sentence｜>
```

Reasoning Turn Layout:
```
<｜begin of sentence｜><｜User｜>{user_message}<｜Assistant｜><think>
{reasoning_content}
</think>
{final_response}<｜end of sentence｜>
```

#### 2. Distilling Reasoning into V3 via Reflective System Prompts
- DeepSeek-V3 was distilled from DeepSeek-R1. However, raw R1 outputs suffered from verbosity, chaotic formatting, and overthinking.
- DeepSeek resolved this by fine-tuning expert models using the tuple:
  ```
  <system prompt, problem, R1 response>
  ```
  The system prompt specifically instructed the model to produce responses enriched with structured reflection, self-verification, and concise execution. Through high-temperature RL, DeepSeek-V3 internalized these reasoning mechanisms without requiring explicit runtime chain-of-thought tokens.

---

### D. Tool-Integrated Reasoning (TIR) & Outer Harness Orchestration

#### 1. The Interleaved Reasoning-Execution Loop (`DeepSeek-Math`)
DeepSeek-Math's evaluation harness (`evaluation/infer/run_tool_integrated_eval.py`) implements Tool-Integrated Reasoning (TIR):
1. The model is prompted:
   > `"Please integrate natural language reasoning with programs to solve the problem above, and put your final answer within \\boxed{}."`
2. Generation streams until the model produces code in a ````python ... ```` block and reaches the stop sequence:
   ```python
   stop_words = [tokenizer.eos_token, "```output"]
   ```
3. The harness pauses generation, extracts the Python snippet (`extract_code`), executes it in a sandboxed process (`PythonExecutor`), and captures stdout or runtime tracebacks.
4. The execution output is wrapped into a delimited block:
   ````
   ```output
   {exec_result}
   ```
   ````
5. The block is appended back into the model's message buffer, and generation resumes. The model inspects the runtime results, corrects errors if present, and continues until it concludes with `\boxed{}`.

#### 2. Dual-Model Agent Architecture: V3 (Harness) + R1 (Solver)
- **DeepSeek-R1's Documented Limitations (Paper Section 5.2):**
  DeepSeek-R1 significantly lags behind DeepSeek-V3 in:
  - Tool/Function calling schema compliance.
  - Multi-turn state tracking across long agent sessions.
  - Strict JSON/schema output generation.
  - Persona stability and complex instruction adherence.
- **Production Harness Pattern:**
  Do not run DeepSeek-R1 as the outer loop controller in complex multi-tool agent harnesses (such as Cline or Claude Code style loops).
  - **Outer Agent Loop:** Deploy **`deepseek-chat` (DeepSeek-V3)** for tool routing, repo exploration, workspace diffing, and file editing.
  - **Reasoning Kernel:** Delegate hard algorithmic subproblems, math proofs, or complex logical bugs to **`deepseek-reasoner` (DeepSeek-R1)** in isolated zero-shot sub-calls.

---

### E. Prompt Caching & Context Architecture (DeepSeek API & SGLang MLA)

#### 1. 64-Token Block Granularity & Automatic Prefix Caching
- **The 64-Token Unit:** Unlike OpenAI and Anthropic (which require 1,024-token minimums to trigger caching), DeepSeek API automatically caches prefixes at **64-token increments**. Any prompt prefix $\ge 64$ tokens is eligible for context caching on distributed storage.
- **Cost Reduction:** Cached input tokens receive up to **90% discount** compared to uncached inputs.
- **Strict Prefix Match Invariance:** Caching is evaluated strictly from token 0. Any mutation in the first 64 tokens (e.g. dynamic timestamps, random IDs, or changing system headers) invalidates 100% of the downstream cache.

#### 2. Prompt Layout Contract for DeepSeek Caching
To maximize cache hits across multi-turn agent turns:
$$\underbrace{\text{Repo Rules + Static Invariants + Tool Schemas}}_{\text{Byte-for-byte frozen prefix (Cache HIT)}} \longrightarrow \underbrace{\text{Session History}}_{\text{Appended turns (Cache HIT)}} \longrightarrow \underbrace{\text{Current Turn Input + Dynamic State}}_{\text{Only uncached tokens}}$$

#### 3. Multi-Head Latent Attention (MLA) Memory Mechanics
- DeepSeek-V3 and Coder-V2 compress the Keys and Values into a low-rank latent vector $\mathbf{c}_t^{KV}$ of dimension 512 (`kv_lora_rank = 512`), along with a decoupled RoPE key $\mathbf{k}_t^R$ of dimension 64 (`qk_rope_head_dim = 64`).
- During inference, local serving frameworks (SGLang, vLLM, LMDeploy) only cache $512 + 64 = 576$ scalar values per token per layer, compared to standard MHA which caches $2 \times n_{\text{heads}} \times d_{\text{head}} = 2 \times 128 \times 128 = 32,768$ values.
- This massive reduction in KV memory bandwidth allows agent harnesses to maintain 128K context windows with high concurrency without running out of GPU VRAM.

---

## 3. Actionable Recommendations for Promptsmith

### Recommendation 1: Update `references/best-practices.md`
1. **Section 3 (Reasoning & Thinking):** Add the **DeepSeek-R1 Zero-Shot Rule** (few-shot prompting consistently degrades reasoning; bar few-shot CoT exemplars for reasoning models) and document the **`<think>\n` prefill trigger**.
2. **Section 4 (Examples):** Document the **Few-Shot Degradation Paradox on RL Reasoning Models** (human exemplars induce shortcut bias and disrupt test-time search exploration).
3. **Section 5 (Sampling Controls):** Document the **Reasoning Model Temperature Paradox** (RL reasoning models degrade under greedy decoding / $T=0.0$; mandate $T=0.6$ for DeepSeek-R1 / o-series).
4. **Section 9 (Token Efficiency):** Add DeepSeek's **64-Token Prefix Caching Granularity** alongside OpenAI and Anthropic 1024-token rules.

#### Proposed Patch for `references/best-practices.md`
```diff
--- a/references/best-practices.md
+++ b/references/best-practices.md
@@ -74,6 +74,15 @@
 
 ## 3. Reasoning, Thinking & Abstraction
 
+**Reasoning Model Zero-Shot Mandate (DeepSeek-R1 & OpenAI o-series):**
+Why: Models trained via large-scale RL (GRPO) explore reasoning trees dynamically. Research proves few-shot CoT exemplars consistently degrade performance by constraining search and inducing shortcut bias.
+- Weak: Providing 3 few-shot math reasoning examples with manual step-by-step thoughts before the problem.
+- Strong: Presenting a direct zero-shot problem statement with format instructions placed at the prompt tail (`Please reason step by step, and put your final answer within \boxed{}.`).
+- Enforcement Trigger: If a reasoning model bypasses its thinking block on simple turns (`<think>\n\n</think>`), prefill the assistant response with `<think>\n` to force test-time deliberation.
+
 ---
 
 ## 4. Examples (Few-Shot & Many-Shot)
@@ -100,6 +109,12 @@
 **Many-Shot In-Context Learning (Anthropic 2024/2025):**
 Why: In 100k+ token context windows, providing 20–50+ real-world examples reliably overrides strong model priors and locks complex formatting or classification schemas that few-shot prompts fail to enforce.
 
+**The Few-Shot Degradation Paradox on RL Models:**
+Why: While standard instruction models benefit from few-shot and many-shot exemplars, pure reasoning models (DeepSeek-R1) suffer performance regression under few-shot prompting.
+- Rule: Use few-shot/many-shot for classification, extraction, and style mimicry on standard models (Claude Sonnet, Gemini Flash, DeepSeek-V3).
+- Rule: Use strict zero-shot for reasoning-heavy tasks on native reasoning models (DeepSeek-R1, o1, o3).
+
 ---
 
 ## 5. Sampling Controls (Google Whitepaper)
@@ -107,8 +122,9 @@
 Match sampling parameters to the task archetype:
 - **Deterministic / Reasoning (Code, Math, Extraction, Schema JSON, Forensics):**
   * `temperature = 0.0` or `0.2` (for standard LLMs: Claude, GPT-4o, Gemini 3.8 Flash, DeepSeek-V3).
-  * Greedy decoding ensures reproducible, logically sound execution.
+  * **Reasoning Model Exception (DeepSeek-R1 / o-series):** Mandate `temperature = 0.6` (range 0.5–0.7). Setting $T=0.0$ or using greedy decoding on RL reasoning models triggers severe degeneration (endless repetition loops, early thinking truncation).
 
 ---
 
 ## 9. Token Efficiency & Context Architecture (2026 Research)
@@ -194,6 +210,11 @@
 - Keep YAML frontmatter and system prompts frozen; never interpolate timestamps, UUIDs, or per-request state into the prefix.
 
+**Cache Granularity Thresholds by Provider:**
+- **Anthropic:** 1,024-token minimum (explicit `cache_control: {"type": "ephemeral"}`).
+- **OpenAI:** 1,024-token minimum (automatic prefix caching with optional `prompt_cache_key`).
+- **DeepSeek:** **64-token minimum** (automatic prefix caching in 64-token blocks, up to 90% discount).
```

---

### Recommendation 2: Update `references/harness-notes.md` (Add DeepSeek Section)
Add a dedicated section detailing DeepSeek-V3 and DeepSeek-R1 harness integration, tool orchestration patterns, special token handling, and caching rules.

#### Proposed Patch for `references/harness-notes.md`
```diff
--- a/references/harness-notes.md
+++ b/references/harness-notes.md
@@ -140,6 +140,26 @@
 - *Settings, not prompt text:* Filesystem containment and tool permissions live in `~/.gemini/antigravity-cli/settings.json` (`request-review`, `proceed-in-sandbox`, `strict`).
 
+## DeepSeek (DeepSeek-V3 & DeepSeek-R1 via API, SGLang, vLLM, or Cline/OpenRouter)
+
+- **Dual-Model Agent Architecture (V3 Harness + R1 Solver):**
+  * DeepSeek-R1 Technical Report (Section 5.2) documents that R1 falls short of V3 in tool/function calling stability, multi-turn state consistency, and complex JSON schema adherence.
+  * **Outer Agent Loop:** Use `deepseek-chat` (DeepSeek-V3) for tool orchestration, repository exploration, file editing, and test execution.
+  * **Reasoning Kernel:** Dispatch complex mathematical derivations, algorithmic design, and intricate bug forensics to `deepseek-reasoner` (DeepSeek-R1) in zero-shot subagent calls.
+- **Zero System Prompt Contract for R1:**
+  * For `deepseek-reasoner` (R1), avoid passing system role messages; bundle instructions and constraints directly into the user message turn.
+  * For `deepseek-chat` (V3), system role messages are fully supported and recommended for repository rules and tool definitions.
+- **The Trailing Space Anomaly on `Assistant:`:**
+  * When formatting prompt templates for DeepSeek tokenizers, never leave a trailing space after `Assistant:`. Appending a space causes language switching (replying in Chinese to English queries), unicode errors, and repetition loops on 16B-Lite and MoE models.
+- **Sampling Configurations:**
+  * `deepseek-reasoner` (R1): Set `temperature = 0.6` (range 0.5–0.7). Never use greedy decoding ($T=0.0$).
+  * `deepseek-chat` (V3): Set `temperature = 0.0` for deterministic code editing and extraction; $0.7$ for creative tasks.
+- **Thinking Bypass Mitigation:**
+  * If R1 bypasses deliberation (`<think>\n\n</think>`), prefill assistant response with `<think>\n`.
+- **64-Token Prefix Caching:**
+  * DeepSeek API caches prefixes at 64-token increments automatically. Keep repository rules, tool declarations, and file envelopes static at the top to secure 90% input token discounts.
+
 ## Other / unknown harness
 
 Cursor, Cline, Aider, Copilot, a raw API loop, or anything unnamed: write to the common core above.
```

---

### Recommendation 3: Update `references/repo-rules.md`
1. Include DeepSeek API and local serving (SGLang/vLLM) in the Tool Discovery Matrix.
2. Add the **Trailing Space Anomaly** and **Zero System Prompt Contract** to the Gotchas & Local Quirks section.

#### Proposed Patch for `references/repo-rules.md`
```diff
--- a/references/repo-rules.md
+++ b/references/repo-rules.md
@@ -16,6 +16,7 @@
 | **`CLAUDE.md`** | Claude Code | Walked up to project root. Checked into repo. | Root (`CLAUDE.md`) |
 | **`GEMINI.md`** | Antigravity (agy), Gemini CLI | Walked up to repo root, subdirectories, or global `~/.gemini/GEMINI.md`. | Subdirectories > Workspace Root > Extensions > Global (`~/.gemini/`) |
 | **`PLANS.md`** | Codex, agy | Referenced in `AGENTS.md` or `.planning/`. Living ExecPlan for multi-hour autonomy. | Working Plan > Root Guidelines |
+| **`DEEPSEEK.md` / `AGENTS.md`** | DeepSeek (V3/R1 via Cline, Roo, SGLang) | Root or user prompt injection. 64-token boundary alignment. | User Turn Envelope (R1) / Root System Prompt (V3) |
 
 > **Context Precedence & Override Boundaries:**
 > - **Google Gemini / agy:** Contextual instructions override default operational behaviors (e.g. style, architectural conventions, tool choices) defined in system prompts, but **cannot** override Core Mandates regarding safety, security, and agent integrity.
@@ -35,6 +36,7 @@
 - <Tool substitution: e.g., sed is sd on this box; use /usr/bin/sed for scripts.>
 - <Platform differences: e.g., Arch uses sshd.service, Debian uses ssh.service.>
 - <Kernel or hardware traps: e.g., avoid bare sensors calls, ASPM bugs.>
+- <Model quirks: never add trailing space after "Assistant:" in DeepSeek prompt templates; enforce temperature=0.6 for R1 reasoning.>
 - <Date or serialization formats: e.g., timestamps MUST be YYYY-MM-DD HH:MM:SS.>
```
