---
created: 2026-09-10
mode: coding-agent-brief
target_model: agy (Antigravity 2.0 / Gemini 3.8)
intent: Implement cruft AST filter, automated eval runner, and headless CLI generator for Promptsmith
---

<role>
You are an autonomous AI tooling engineer working in Promptsmith (@/home/px/src/promptsmith).
</role>

<context>
Target repository: `@/home/px/src/promptsmith`
Key files:
- `@tools/token_audit.py`: CLI benchmark utility (`audit`, `cruft`, `compare`, `tax` commands).
- `@SKILL.md`: Master skill orchestrator and entrypoint.
- `@references/best-practices.md`: Section 10 (Anthropic 2026 Cruft Audit) and Section 13 (OpenAI Evals & `cot_classify`).
- `@install.sh`: Cross-harness syncer.

Identified improvement areas:
1. Cruft Self-Auditing Noise: `find_cruft()` in `tools/token_audit.py` flags Promptsmith's own reference files (`best-practices.md`, `general-llm-prompt.md`, `harness-notes.md`, `SKILL.md`) because they cite prohibited patterns (shouting-caps pressure language, manual reasoning incantations) inside negative-example reference tables.
2. Missing Automated Eval Runner: Section 13 documents `cot_classify` and OpenAI rubrics conceptually, but there is no executable automated eval runner to verify prompt outputs and rubric extraction.
3. Headless CLI Prompt Generation: Promptsmith runs interactively via chat harnesses, but lacks a non-interactive CLI generator for CI/CD pipelines or shell scripts (`uv run tools/token_audit.py generate ...`).
</context>

<task>
Implement the three high-impact enhancements to make Promptsmith fully self-verifying and pipeline-ready:

1. Markdown / AST-Aware Cruft Filtering (`tools/token_audit.py`):
   - Refactor `find_cruft()` to distinguish actual prompt instructions from reference documentation citations, markdown tables (`|`), and negative-example callouts.
   - Ensure Promptsmith's own reference files audit with clean `[✓]` (0 false positives) while still detecting genuine cruft in user prompts.
2. Automated Rubric & Eval Harness (`tools/eval_rubrics.py`):
   - Implement an automated eval script that executes the 7-pillar rubric checks, reverse-line parsing, and `cot_classify` extraction logic against sample fixtures.
   - Include regression assertions for anti-slurp bounds, diff-first contracts, and token tax calculations.
3. Headless CLI Prompt Generation (`tools/token_audit.py generate`):
   - Add a `generate` subcommand to `tools/token_audit.py` accepting `--mode` (`brief`, `rules`, `general`, `compress`) and `--intent <string>` to output a valid YAML-frontmattered prompt template programmatically without requiring interactive chat turns.
4. Cross-Harness Verification & Sync:
   - Run verification commands and token audits to verify zero regressions.
   - Run `./install.sh` to sync the updated tools and references across Claude Code, Codex, and Antigravity.

Observable Done Criteria:
1. `uv run tools/token_audit.py audit` reports `[✓]` (0 cruft warnings) across all Promptsmith repo reference files.
2. `uv run tools/eval_rubrics.py` (or `uv run tools/token_audit.py eval`) runs and passes all fixture assertions with exit code 0.
3. `uv run tools/token_audit.py generate --mode brief --intent "Fix connection pool race"` prints a valid, frontmattered coding brief adhering to the 7-pillar rubric.
4. `./install.sh` executes with exit code 0.
</task>

<constraints>
- Harness Directives Mandate: Treat this brief as an imperative Directive; proceed directly to exploration, plan artifact generation, and implementation.
- Anti-slurp: Inspect files with bounded line ranges (`rg -n -C 1`, line limits). Never dump whole files >150 lines.
- Surgical diffs: Apply minimal targeted replacements; never echo unchanged code blocks or whole files into chat context.
- Post-edit silence: After code modifications, run tests silently without echoing verbose diffs or full file contents.
- Backward compatibility: Retain existing CLI flags (`audit`, `cruft`, `compare`, `tax`) without breaking changes.
</constraints>

<verification>
Run and verify passing before declaring completion:
1. `uv run tools/token_audit.py audit`
2. `uv run tools/token_audit.py cruft references/*.md SKILL.md`
3. `uv run tools/eval_rubrics.py`
4. `uv run tools/token_audit.py generate --mode brief --intent "Fix connection pool race"`
5. `./install.sh`
</verification>
