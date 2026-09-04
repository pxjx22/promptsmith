---
name: promptsmith
description: Craft or improve a prompt for an LLM or coding agent following prompt-engineering best practices. Use this skill when the user explicitly asks to write, draft, refine, or critique a prompt (e.g. `/promptsmith`, `$promptsmith`, or "help me write a prompt for…"). Not for answering the underlying task itself.
metadata:
  version: 2.0.0
---

# Promptsmith

Turn a natural-language description into a well-formed prompt, applying
established prompt-engineering practice. Works for three target modes:

- **Coding-agent brief** — a task for Claude Code, Codex, agy, or similar
  (features, forensics/investigations, bugfixes, audits, refactors, frontend).
- **Repository rules & system instructions** — persistent instructions for
  agents (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or custom system prompts).
- **General LLM prompt** — single-shot or reusable prompts for analysis,
  structured JSON extraction, classification, writing, or transformation.

## When to use

Only when the user explicitly asks for a prompt to be written, drafted,
refined, or critiqued. Do **not** invoke this to answer the underlying
task — if someone asks "classify these tickets", just do it; if they ask
"write me a prompt that classifies tickets", use this skill.

## Workflow

Follow these four steps in order.

### 1. Set the mode

Infer **coding-agent brief**, **repo-rules**, or **general LLM prompt**
from the request. Confirm with the user only if genuinely ambiguous. If the
user pasted an existing prompt to improve, pick the matching mode and note
that this is an *improve* run, not a *create* run.

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
- Otherwise ask **up to 4** questions, in a **single numbered round**,
  each with a recommended default answer so the user can reply "all
  defaults". Never ask a second round — draft with best assumptions and
  let step 4's refinement pass catch the rest.

### 3. Draft

Read `references/best-practices.md` and the mode reference, then write the
prompt applying the checklist below. For a coding brief, read
`references/harness-notes.md` for the resolved harness and apply its
adjustments:
- **Claude Code (Fable 5.1 / Opus 5 / Sonnet 5):** Ask for progress notes on Fable 5.1;
  demand conciseness on Opus 5; bar unprompted repo-root scratch files; guard against test-gaming.
- **Codex (GPT-5.6 series: terra / sol):** Lean into senior-engineer autonomy; use
  natural 1–2 sentence preambles without rigid upfront plans that cause early stopping;
  enforce solver tools (`rg`, `git`, `apply_patch`) and strict error handling; protect dirty worktrees.
- **agy (Antigravity 2.0 / Gemini 3.8):** Verification loop is primary; explore -> plan artifact -> execute;
  hydrate with `@path` and pasted media (`ctrl+v`); parallel background subagent fan-out for broad sweeps.

**For an Improve run:** evaluate the draft against the 6-pillar rubric:
1. Goal & Done-Criteria
2. Information Hierarchy & XML Framing (data *before* instructions)
3. Positive Framing & Rationale
4. Guardrails (scope ceiling, anti-gaming, no file sprawl)
5. Grounding & Verification Loop
6. Target Harness Alignment

Provide 3–6 bullets naming what changed and why.

### 4. Deliver

1. Print the finished prompt in a fenced code block.
2. Follow it with 2–4 bullets — "principles applied" — naming the main
   best-practice moves. (These are for the chat only; they do not go in
   the saved file.)
3. Save it:
   - **Coding brief:** offer `./prompts/<slug>.md` in the current project
     (create `./prompts/` if accepted); if declined or outside a project,
     save to `~/prompts/<slug>.md`.
   - **Repository rules:** save directly to target root as `AGENTS.md`,
     `CLAUDE.md`, or `GEMINI.md`.
   - **General prompt:** save to `~/prompts/<slug>.md` (the unified personal vault).
   - `slug` = `<kebab-goal>` (concise, descriptive kebab-case topic name, e.g. `monolith-sync-remediation.md`). Do NOT prefix with the date — the creation date is tracked in the YAML frontmatter.
   - If target file exists, ask: overwrite, or save as `<slug>-2`?
   - File contents = YAML frontmatter then the prompt body only:
     ```markdown
     ---
     created: YYYY-MM-DD
     mode: coding-agent-brief | repo-rules | general-llm-prompt
     target_model: <if known, else omit>
     intent: <one line>
     ---

     <prompt body>
     ```
4. Offer exactly **one** refinement pass. If accepted, revise and overwrite the same file.

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

## References

- `references/coding-agent-brief.md` — templates (base + 5 archetypes: forensics, feature, bugfix, review, frontend) + question pool.
- `references/repo-rules.md` — templates and question pool for `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
- `references/general-llm-prompt.md` — templates (base + JSON schema + triage) + question pool + 6-pillar rubric.
- `references/best-practices.md` — one-page cheatsheet: each principle with rationale and example.
- `references/harness-notes.md` — per-harness conventions (Claude Code Fable 5.1/Opus 5/Sonnet 5, Codex GPT-5.6, agy Antigravity 2.0 / Gemini 3.8).

Read only the mode reference you need, plus the cheatsheet, plus
`harness-notes.md` when a coding brief names its target harness.

## Maintenance

The canonical copy lives at `~/.claude/skills/promptsmith/`. After editing
it, run `./sync-promptsmith.sh` to copy it into Codex (`~/.codex/skills/`)
and agy (`~/.gemini/config/skills/`) directories.
