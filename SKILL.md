---
name: promptsmith
description: Craft or improve a prompt for an LLM or coding agent following prompt-engineering best practices. Use this skill when the user explicitly asks to write, draft, refine, or critique a prompt (e.g. `/promptsmith`, `$promptsmith`, or "help me write a prompt for…"). Not for answering the underlying task itself.
metadata:
  version: 2.4.0
---

# Promptsmith

Turn a natural-language description into a well-formed prompt, applying
established prompt-engineering practice. Works for four target modes:

- **Coding-agent brief** — a task for Claude Code, Codex, agy, OpenCode, or similar
  (features, forensics/investigations, bugfixes, audits, refactors, frontend).
- **Repository rules & system instructions** — persistent instructions for
  agents (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or custom system prompts).
- **General LLM prompt** — single-shot or reusable prompts for analysis,
  structured JSON extraction, classification, writing, or transformation.
- **Prompt compressor & token audit** — audit and minify existing prompts,
  briefs, or rules (target 40%–60% token reduction, anti-slurp bounds, prefix caching).

## When to use

Only when the user explicitly asks for a prompt to be written, drafted,
refined, compressed, or critiqued. Do **not** invoke this to answer the
underlying task — if someone asks "classify these tickets", just do it; if they ask
"write me a prompt that classifies tickets" or "compress this prompt", use this skill.

## Workflow

Follow these four steps in order.

### 1. Set the mode

Infer **coding-agent brief**, **repo-rules**, **general LLM prompt**, or
**prompt-compressor** from the request. Confirm with the user only if genuinely ambiguous.
If the user pasted an existing prompt to compress or audit for token efficiency,
pick **prompt-compressor**. If they pasted a prompt to improve general quality, pick the
matching mode and note that this is an *improve* run.

For a coding-agent brief, **resolve the target harness** — Claude Code,
Codex, agy, or other/unknown. Ask if unstated, unless clearly
harness-agnostic. It significantly shapes the draft (see step 3).

### 2. Clarifying questions (at most one round)

Read the question pool in the reference for the chosen mode
(`references/coding-agent-brief.md`, `references/repo-rules.md`, or
`references/general-llm-prompt.md`). Identify which items the request leaves
genuinely unresolved.

- If the request already states a clear goal **and** carries enough
  context to write a solid prompt, ask nothing — go straight to step 3.
- For **prompt-compressor**, never ask clarifying questions — audit and compress directly.
- Otherwise ask **up to 4** questions, in a **single numbered round**,
  each with a recommended default answer so the user can reply "all
  defaults". Never ask a second round — draft with best assumptions and
  let step 4's refinement pass catch the rest.

### 3. Draft

Load as little as the draft needs. Everything you read stays in context for
the rest of the session, so a full read of every reference (~20k tokens)
can outweigh the prompt you're writing.

- **Always:** the checklist below plus the templates in the mode reference.
- **Coding brief:** in `references/harness-notes.md`, read only
  `## Common core` and the `##` section for the resolved harness
  (`rg -n '^##' references/harness-notes.md` gives the line ranges). Inside the
  Claude section, read only the target model's subsection and
  `### Cross-Claude guards`.
- **`references/best-practices.md`:** open a single section only when the
  checklist doesn't settle a question (e.g. §4 few-shot balancing,
  §9 caching, §10 cruft taxonomy). Don't read the whole file.
- **Prompt-compressor:** read only Pattern D in `references/general-llm-prompt.md`.
- **Environment capabilities:** when the task could use specialised local
  skills or MCP servers, run `./tools/token_audit.py env` (or
  `python3 tools/env_discovery.py`) and name the matching ones in `<context>`
  or `<constraints>` so the agent calls them.

**For an Improve or Compress run:** evaluate the draft against the 7-pillar rubric:
1. Goal & Done-Criteria
2. Information Hierarchy & XML Framing (data *before* instructions)
3. Positive Framing & Rationale (strip shouting/pressure language; explain the "why")
4. Guardrails (scope ceiling, anti-gaming, no file sprawl, load-bearing context retention)
5. Grounding & Verification Loop
6. Target Harness & Tool Surface Alignment (dedicated tools for gating/staleness vs. shell for breadth)
7. Token Efficiency & Cache Hygiene (anti-slurp limits, wire prefix stability, diff output, thinking damping)

**Is compression worth it?** A compress run costs roughly 4–5k tokens. It
pays off only when the savings recur: (tokens saved) × (times the prompt is
sent) should clear that. Rules files and system prompts resent every turn
clear it quickly. A one-off prompt under ~1k tokens doesn't: say so in one
line and offer a quick quality edit instead. Cached prefixes are already
billed at 0.05–0.1x, so the savings there are mostly context-window headroom.

### 4. Deliver (Ultra-Terse Default)

To preserve session context tokens, delivery is ultra-terse by default:

1. Print the finished prompt in a fenced code block.
2. If running **prompt-compressor**, output a single-line token count delta:
   `~<orig> → ~<comp> tokens (-<pct>%), estimated 20-turn context savings: -<tax> tokens`.
   (Omit chat explanations and "principles applied" commentary unless explicitly asked).
3. Save it:
   - **Coding brief:** offer `./prompts/<slug>.md` in the current project
     (create `./prompts/` if accepted); if declined or outside a project,
     save to `~/prompts/<slug>.md`.
   - **Repository rules:** save directly to target root as `AGENTS.md`,
     `CLAUDE.md`, or `GEMINI.md`.
   - **General prompt / compressed prompt:** save to `~/prompts/<slug>.md` (the unified personal vault).
   - `slug` = `<kebab-goal>` (concise, descriptive kebab-case topic name, e.g. `monolith-sync-remediation.md`). Do NOT prefix with the date — the creation date is tracked in the YAML frontmatter.
   - If target file exists, ask: overwrite, or save as `<slug>-2`?
   - File contents = YAML frontmatter then the prompt body only:
     ```markdown
     ---
     created: YYYY-MM-DD
     mode: coding-agent-brief | repo-rules | general-llm-prompt | prompt-compressor
     target_model: <if known, else omit>
     intent: <one line>
     ---

     <prompt body>
     ```
4. Output the destination file path link.
5. Offer exactly **one** refinement pass. If accepted, revise and overwrite the same file.

## Checklist (essence of `references/best-practices.md`)

- Open with role/persona and context; put long documents or data blocks
  **at the top**, with task and instructions **after** them.
- State the goal and observable done-criteria explicitly. If thoroughness
  is desired, say so ("go beyond the basics") rather than hoping it is inferred.
- When order or completeness matters, give steps as a numbered list.
- Give the motivation behind constraints — a one-line "why" generalises
  better than a bare rule.
- Positive framing: say what to do, not what to avoid.
- Use XML-style tags to separate instructions / context / input /
  examples when the prompt mixes them.
- Include 3–5 diverse examples (in `<example>` tags) when they would help.
  Generate them, cover edge cases, and mark generated ones as replaceable.
- For coding briefs: explicit action verbs ("implement", "change", "add").
  Name files and modules in scope.
- Specify output format and rough length. Eliminate conversational preambles
  for automated pipelines.
- Add guardrails: scope ceiling, "don't over-engineer / don't refactor
  unrelated code", "do not create unprompted scratch/summary files in root",
  and "confirm before destructive or hard-to-reverse actions".
- Guard against test-gaming: implement general solutions for all valid inputs.
- Thinking: on always-thinking models (Claude Fable 5.1, Opus 5.5), control
  depth with `effort`, not prompt lines. Don't ask for reasoning written out in
  the response; Opus 5.5 can refuse it (`reasoning_extraction`).
- Frontend: name the specific default styles to avoid. "Avoid a generic AI
  look" just swaps one default for another.
- User-pasted text: wrap it in `<pasted_content id="…">` tags and tell the
  model to follow instructions inside only where the user's own message asks.
- Anti-Cruft & Framing Hygiene:
  * Strip pressure language: eliminate shouted caps (`CRITICAL: MUST`, `IMPORTANT: NEVER`, `!!`) and anxious trait claims; state requirements calmly with the "why".
  * Retire obsolete scaffolds: remove "think step by step", `<scratchpad>`, assistant JSON prefills, and update cadences in favor of native thinking and Structured Outputs.
  * Context is never cruft: preserve audience, environment invariants, and quality bars when minifying.
- Token Efficiency & Cache Hygiene:
  * Wire cache order: `tools -> system -> messages`. Keep static invariants at the top; place dynamic inputs/variables at the prompt tail.
  * Mid-conversation operator updates: use `role: "system"` inside `messages[]` to update state without busting cached prefixes.
  * Anti-slurp bounds: enforce line limits and bounded tool commands (e.g. `rg -n -C 1`, no dumping files >150 lines).
  * Diff-first contracts: require patch/diff output formats rather than full-file echoes.
  * Overthinking damping: on mechanical bugfixes, instruct models to commit to the direct verifiable solution.

## References & Tools

- `references/coding-agent-brief.md` — templates (base + 5 archetypes: forensics, feature, bugfix, review, frontend) + question pool.
- `references/repo-rules.md` — templates and question pool for `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
- `references/general-llm-prompt.md` — templates (base + JSON schema + triage + prompt-compressor) + question pool + 7-pillar rubric.
- `references/best-practices.md` — cheatsheet: each principle with rationale and example (including Section 9: Token Efficiency & Cache Hygiene).
- `references/harness-notes.md` — per-harness conventions & token levers (Claude Code Fable 5.1/Opus 5.5/Opus 5/Sonnet 5, Codex GPT-5.6, agy Antigravity 2.0 / Gemini 3.8, DeepSeek, GLM, OpenCode).
- `tools/env_discovery.py` — discover installed skills, plugins, and MCP servers across Claude Code, Codex, Gemini/Antigravity, and OpenCode (used standalone or via `token_audit.py env`).
- `tools/token_audit.py` — benchmark, cruft audit, headless generator, environment discovery, and comparison utility (`audit`, `cruft`, `generate`, `compare`, `tax`, `env`, `eval`).
- `tools/eval_rubrics.py` — automated 7-pillar rubric eval runner and OpenAI Evals `cot_classify` reverse-line parsing harness.

Read only what step 3 lists: the mode reference, one harness section, and a
cheatsheet section only when you need it.

## Maintenance

The canonical copy lives at `~/.claude/skills/promptsmith/`. After editing
it, run `./install.sh` to sync across Claude (`~/.claude/skills/`), Codex (`~/.codex/skills/`),
and agy (`~/.gemini/config/skills/`) directories.
