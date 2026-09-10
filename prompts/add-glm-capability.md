---
created: 2026-09-10
mode: coding-agent-brief
target_model: agy (Antigravity CLI 2.0 / Gemini 3.8)
intent: Scrape and synthesize GLM-5.3 intelligence and integrate GLM reasoning, coding, and harness capabilities into Promptsmith
---

<role>
You are an autonomous research engineer and agent harness specialist working in Promptsmith (@/home/px/src/promptsmith). Your role is to explore, extract, synthesize, and integrate prompt engineering intelligence, reasoning model paradigms, and agent harness conventions for GLM-5.3 into Promptsmith.
</role>

<context>
Target repository: `@/home/px/src/promptsmith`
Reference models for synthesis and harness integration:
- `@scrapes/deepseek-intelligence.md` (benchmark for scraped intelligence reports)
- `@scrapes/google-gemini-intelligence.md` (synthesis structure standard)
- `@prompts/scrape-deepseek-intelligence.md` (precedent for multi-phase extraction briefs)
- `@references/harness-notes.md` (harness configuration and model-specific levers)
- `@references/best-practices.md` (Section 8 Harness Summary Cheatsheet)
- `@tools/token_audit.py` (benchmark, cruft audit, and prompt generator)
- `@tools/eval_rubrics.py` (automated 7-pillar rubric test suite)
- `@install.sh` (cross-harness syncer across Claude, Codex, and agy)

Primary intelligence sources:
1. Z.ai Official Developer Documentation: `https://docs.z.ai/guides/llm/glm-5.3`
   - Model profile: GLM-5.3 by Z.ai (Zhipu AI / THUDM lineage), released August 2026.
   - Base architecture: 743B parameter base model, with performance gains achieved via post-training (SAO RL, slime framework, executable task environments).
   - Context window: 1,000,000 tokens (1M tokens); maximum generation ceiling: 128,000 tokens (128K tokens).
   - Reasoning architecture: Always-on reasoning (`thinking: {type: "enabled"}`). Disabling reasoning is not supported and returns errors.
   - Reasoning effort controls: `reasoning_effort: "low" | "high" | "max"`. Default is `max` for software engineering and complex coding tasks; `low` for lightweight transformations.
   - Sampling controls: Recommended `temperature = 1.0` for reasoning generation.
   - Dual protocol & endpoint compatibility:
     * OpenAI Chat Completion Protocol: `https://api.z.ai/api/coding/paas/v4`
     * OpenAI Response Protocol: `https://api.z.ai/api/v1`
     * Anthropic Message Protocol: `https://api.z.ai/api/anthropic`
   - Streaming delta contract: Separate streaming deltas for reasoning (`delta.reasoning_content`) and user-facing output (`delta.content`).
   - Token efficiency & coding profile: 50% coding gain over GLM-5.2; 31.4% on Code Bench (High) vs Claude Opus 4.8 (29.5%) consuming ~50,000 tokens per task vs Opus's ~120,000 tokens.
   - Flash variant: `glm-5.3-flash` (320B total, 18B active MoE, hybrid sparse/linear attention, mHC, open weights under MIT, tested as "Ox Alpha").
2. GLM-5.3 Client & Weights Hub: `https://github.com/GLM-5-3-app/GLM-5.3`
   - Lightweight standalone desktop client and agent environment with local project library.
   - Drop-in agent configurations for Claude Code, Cursor, and Cline using OpenAI and Anthropic compatible base URLs.

Tool invariants & storage targets:
- Cloned/curated reference material directory: `@scrapes/glm/`
- Target synthesis document: `@scrapes/glm-intelligence.md`
- Core reference updates: `@references/harness-notes.md` and `@references/best-practices.md`
- Tooling updates: `@tools/token_audit.py` and `@tools/eval_rubrics.py`
</context>

<task>
Scrape, synthesize, and integrate GLM-5.3 capability into Promptsmith end-to-end. Execute the following directives to completion:

1. Curate and Extract Source Material into `scrapes/glm/`:
   - Fetch and curate key guides, API schemas, and harness configs from `https://docs.z.ai/guides/llm/glm-5.3` and `https://github.com/GLM-5-3-app/GLM-5.3`.
   - Prune build artifacts, git metadata (`.git/`), and large binaries to preserve clean repository hygiene.

2. Author the Intelligence Synthesis Document (`scrapes/glm-intelligence.md`):
   - Adhere to the benchmark structure established in `scrapes/deepseek-intelligence.md`.
   - Include:
     * Scraped Sources Overview table (Source, Path in `scrapes/`, Files, Primary Value for Promptsmith).
     * Always-On Reasoning Dynamics (mandatory `thinking: {type: "enabled"}`, reasoning effort calibration between `low`, `high`, and `max`).
     * Dual Protocol Architecture (OpenAI `/coding/paas/v4` and Anthropic `/anthropic` drop-in compatibility without prompt refactoring).
     * Token Economics & Efficiency (1M context window, 50k tokens/task coding benchmark profile vs Opus 4.8, context caching dynamics).
     * Prompt Construction Patterns (zero-shot problem description, tail-placed output format constraints, avoiding manual CoT scripts).
     * Streaming Delta Contracts (`reasoning_content` vs `content` handling).

3. Integrate GLM-5.3 into Promptsmith References:
   - `references/harness-notes.md`: Add a dedicated section for GLM-5.3 (Z.ai GLM Coding Plan, Cline/Cursor/Claude Code drop-in), documenting context limits, mandatory thinking flags, reasoning effort calibration, sampling parameters ($T=1.0$), and endpoint routing.
   - `references/best-practices.md`: Add GLM-5.3 entry to Section 8 (Harness Summary Cheatsheet).

4. Extend Promptsmith Tooling:
   - `tools/token_audit.py`: Update `generate_prompt()` and CLI argument parsing to support GLM-5.3 as a recognized target model (e.g. `--target-model "GLM-5.3 (Z.ai)"` or `--target-model glm`).
   - `tools/eval_rubrics.py`: Add a regression assertion verifying GLM-5.3 prompt generation and rubric compliance.

5. Cross-Harness Verification & Sync:
   - Verify that all reference files audit with clean `[✓]` (0 cruft warnings).
   - Verify that `tools/eval_rubrics.py` passes all regression checks.
   - Run `./install.sh` to synchronize updates across Claude Code, Codex, and Antigravity directories.

Observable Done Criteria:
1. `scrapes/glm-intelligence.md` is authored with complete tables, citations, and actionable synthesis.
2. `references/harness-notes.md` contains a comprehensive GLM-5.3 harness section.
3. `references/best-practices.md` includes the GLM-5.3 entry in Section 8.
4. `uv run tools/token_audit.py audit` reports `[✓]` (0 cruft warnings) across all reference and prompt files.
5. `uv run tools/eval_rubrics.py` passes all test assertions with exit code 0.
6. `uv run tools/token_audit.py generate --mode brief --intent "Implement GLM feature" --target-model "GLM-5.3"` outputs a valid frontmattered brief.
7. `./install.sh` executes with exit code 0.
</task>

<workflow>
Execute across four distinct phases:

Phase 1 (Ingestion & Source Curation):
1. Download documentation pages and repository reference files (`llms.txt`, README, schemas) into `scrapes/glm/`.
2. Prune any `.git/` directories or files larger than 500KB.

Phase 2 (Intelligence Synthesis):
1. Analyze extracted materials for repeatable prompt-engineering rules, reasoning effort levers, endpoint compatibility, and token economy.
2. Author `@scrapes/glm-intelligence.md` adhering to the standard set by `@scrapes/deepseek-intelligence.md`.

Phase 3 (Reference & Tooling Integration):
1. Update `@references/harness-notes.md` with the dedicated GLM-5.3 section.
2. Update `@references/best-practices.md` with the Section 8 GLM summary.
3. Update `@tools/token_audit.py` to recognize GLM models in `generate_prompt()`.
4. Update `@tools/eval_rubrics.py` with test coverage for GLM generation.

Phase 4 (Validation, Token Audit & Sync):
1. Run `uv run tools/token_audit.py audit` and `uv run tools/token_audit.py cruft references/*.md SKILL.md`.
2. Run `uv run tools/eval_rubrics.py`.
3. Test `uv run tools/token_audit.py generate --mode brief --intent "Implement billing webhook" --target-model "GLM-5.3"`.
4. Run `./install.sh` to sync across all agent harnesses.
</workflow>

<constraints>
- Harness Directives Mandate: Treat this brief as an imperative Directive; proceed directly to exploration, plan artifact generation, and implementation without stalling in advisory mode.
- Context Compression: Delegate repetitive multi-file sweeps or verbose tool outputs to sub-agents to preserve parent context.
- Anti-slurp bounds: Inspect files with bounded line ranges (`rg -n -C 1`, line limits). Never dump whole files >150 lines.
- Surgical diffs: Apply minimal targeted replacements; never echo unchanged code blocks or whole files into chat context.
- Post-edit silence: Emit a concise one-sentence intent before tool execution, but provide no verbose summaries after file modifications.
- Scope ceiling: Confine modifications strictly to `scrapes/glm*`, `references/harness-notes.md`, `references/best-practices.md`, `tools/token_audit.py`, `tools/eval_rubrics.py`, and sync via `install.sh`. Do not refactor unrelated modules.
- Backward compatibility: Retain all existing CLI flags and harness sections without breaking changes.
</constraints>

<verification>
Execute these checks sequentially to verify the implementation:
1. Verify synthesized intelligence document:
   `test -f scrapes/glm-intelligence.md && grep -q "## 1. Scraped Sources Overview" scrapes/glm-intelligence.md && echo "Intelligence doc OK"`
2. Verify harness notes and best practices:
   `grep -q "## GLM-5.3" references/harness-notes.md && grep -q "GLM-5.3" references/best-practices.md && echo "Harness notes OK"`
3. Verify zero cruft across Promptsmith references:
   `uv run tools/token_audit.py cruft references/*.md SKILL.md`
4. Run full rubric regression suite:
   `uv run tools/eval_rubrics.py`
5. Verify CLI generation for GLM:
   `uv run tools/token_audit.py generate --mode brief --intent "Implement webhook handler" --target-model "GLM-5.3"`
6. Verify cross-harness sync:
   `./install.sh`
Iterate until all verification checks pass cleanly with exit code 0.
</verification>

<output>
1. Table of scraped GLM-5.3 sources and file counts in `scrapes/glm/`.
2. Overview of synthesized intelligence in `scrapes/glm-intelligence.md`.
3. Minimal diff excerpts of updates to `references/harness-notes.md`, `references/best-practices.md`, and `tools/token_audit.py`.
4. Verification command outputs confirming 0 cruft warnings and green eval test passes.
</output>
