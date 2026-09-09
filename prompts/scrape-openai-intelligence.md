---
created: 2026-09-09
mode: coding-agent-brief
target_model: agy (Antigravity CLI 2.0 / Gemini 3.8)
intent: Scrape and synthesize OpenAI GitHub repos for prompt engineering patterns, agent harness mechanics, and LLM evaluation intelligence
---

<role>
You are an autonomous research engineer and agent harness specialist. Your role is to explore, extract, and synthesize prompt engineering intelligence, agent orchestration patterns, system instruction architectures, and evaluation rubrics from public OpenAI GitHub repositories for Promptsmith.
</role>

<context>
Target workspace: `@/home/px/src/promptsmith`
Reference model for output:
- `@scrapes/google-gemini-intelligence.md` (established benchmark for how scraped intelligence is summarized and structured for Promptsmith)

Target repositories under `https://github.com/openai`:
- `openai/openai-cookbook`: Prompt engineering examples, system prompt patterns, structured outputs, chain-of-thought, function calling, evaluation recipes
- `openai/evals`: Evals framework, benchmark prompt formats, model-based grading templates, rubrics
- `openai/swarm`: Multi-agent orchestration, routine/handoff patterns, agent system prompt composition, tool use conventions
- `openai/openai-python`: Tool call schemas, structured output parsing, message formatting conventions
- Official reasoning model guides (o1, o3 series, GPT-5/6 series prompting): Prompt structuring without manual CoT pressure, goal-oriented system prompts, constraint handling

Environment & tool invariants:
- Use `gh` CLI (`gh repo view`, `gh api`), `git clone --depth 1`, `curl`, and targeted Python/ripgrep inspection.
- Target output directory for cloned/curated reference files: `@scrapes/openai/`
- Target synthesis document: `@scrapes/openai-intelligence.md`
</context>

<task>
Scrape, extract, and synthesize prompt engineering and agent harness intelligence from OpenAI's public repositories. Execute the following directives to completion:

1. Audit and map prompt-engineering, agent-harness, evaluation, and system-instruction assets across target OpenAI repositories (`openai-cookbook`, `evals`, `swarm`, `openai-python`).
2. Perform shallow, selective extraction of key prompt references, system prompt templates, agent handoff schemas, and evaluation rubrics into `scrapes/openai/` (e.g., `scrapes/openai/cookbook/`, `scrapes/openai/evals/`, `scrapes/openai/swarm/`), pruning heavy build artifacts, test fixtures, large dataset dumps, and git metadata.
3. Synthesize findings into `scrapes/openai-intelligence.md`, following the structure established in `scrapes/google-gemini-intelligence.md`:
   - Scraped Repositories Overview table (Repo, Path in `scrapes/`, Primary Value for Promptsmith).
   - Core Prompting Intelligence for Promptsmith:
     * System Prompt Design & Developer Role conventions.
     * Structured Outputs & JSON schema compliance patterns.
     * Reasoning Model Prompting Rules (o1/o3/GPT-5+ vs standard completion models: CoT damping, instruction placement, constraint handling).
     * Multi-Agent Handoffs & Routines (Swarm patterns, agent communication protocols).
     * Evaluation & Token/Context Practices (eval prompt design, model grading, context caching).
   - Concrete, actionable update recommendations for Promptsmith's `references/best-practices.md`, `references/harness-notes.md` (Codex/OpenAI section), and `references/repo-rules.md`.
4. Verify that all extracted files in `scrapes/openai/` are clean markdown/code and that `scrapes/openai-intelligence.md` contains complete, grounded citations and cross-references.
</task>

<workflow>
Execute across four distinct phases:

Phase 1 (Discovery & Triage):
1. Query the GitHub API via `gh api` or `gh repo view` to identify repository structures and key paths.
2. Identify high-value targets:
   - In `openai-cookbook`: `examples/` (prompting, function calling, structured outputs), system prompt guides.
   - In `evals`: `evals/registry/`, prompt templates, grading rubrics.
   - In `swarm`: `swarm/core.py`, routine patterns, agent handoff mechanics.
   - In reasoning documentation: o1/o3 prompting recommendations.

Phase 2 (Targeted Extraction via Sub-Agent Delegation):
1. Delegate repo-specific deep sweeps to sub-agents (acting as context compressors) to run shallow clones (`git clone --depth 1`) or download raw files into `scrapes/openai/<repo>/`. Sub-agent multi-turn traces must collapse into compact summaries to protect parent context.
2. Clean and prune each cloned repository immediately: remove `.git/` directories, large JSONL dataset files, audio/video/image assets, and build artifacts. Keep only markdown guides, notebooks, prompt templates, and core python schemas.

Phase 3 (Synthesis & Intelligence Extraction):
1. Analyze extracted materials for repeatable prompt engineering patterns, harness protocols, token optimization levers, and reasoning model behaviors.
2. Author `@scrapes/openai-intelligence.md` adhering to the standard set by `@scrapes/google-gemini-intelligence.md`.

Phase 4 (Verification & Link Audit):
1. Verify that all local file references in `@scrapes/openai-intelligence.md` point to existing files in `scrapes/openai/`.
2. Confirm that no git metadata or files exceeding 500KB linger in `scrapes/openai/`.
</workflow>

<constraints>
- Directives Mandate: Maintain an active implementation posture. Do not stop in read-only advisory inquiry mode.
- Context Compression: Delegate high-volume directory sweeps and cloning tasks to sub-agents to preserve parent session context.
- Anti-slurp bounds: Inspect files using targeted line bounds (`view_file` with `StartLine`/`EndLine`) and bounded commands (`rg -n -C 1`). Never dump whole files exceeding 150 lines into context.
- Surgical diffs & output contracts: Apply minimal targeted diffs and concise excerpts; never echo full unmodified reference files.
- Clean storage: Prune `.git` directories and dataset dumps (>500KB) from `scrapes/openai/` to keep the workspace lightweight.
- Scope ceiling: Confine modifications strictly to `scrapes/openai/` and `scrapes/openai-intelligence.md`. Do not modify existing `references/`, `tools/`, or repo configuration during this task.
- Post-edit silence: Emit a concise one-sentence intent before tool execution, but provide no verbose summaries after file modifications.
</constraints>

<verification>
Execute these checks sequentially to verify the extraction:
1. Verify synthesized intelligence document:
   `test -f scrapes/openai-intelligence.md && grep -q "## 1. Scraped Repositories Overview" scrapes/openai-intelligence.md && echo "Intelligence doc OK"`
2. Verify curated repository directories:
   `ls -ld scrapes/openai/cookbook scrapes/openai/evals scrapes/openai/swarm 2>/dev/null || ls -ld scrapes/openai/*`
3. Verify no lingering git metadata:
   `find scrapes/openai/ -name ".git" | grep . && echo "Found .git (FAIL)" || echo "No .git dirs (PASS)"`
4. Verify file sizes:
   `find scrapes/openai/ -size +500k`
Iterate until all verification checks pass cleanly.
</verification>

<output>
1. Table of scraped repositories with paths and file counts.
2. Key architectural findings synthesized into `scrapes/openai-intelligence.md`.
3. Concrete recommendations and minimal patch diffs for updating Promptsmith's `references/best-practices.md` and `references/harness-notes.md`.
</output>
