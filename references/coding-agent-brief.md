# Coding-agent brief

A prompt that hands a coding task to an autonomous agent (Claude Code,
Codex, agy, Cursor, etc.). The agent can read the repo and run tools, so
the brief's job is to fix the goal, the boundaries, and the definition of
done — not to spell out every line.

## Always resolve first: the target harness

Before drafting a coding brief, establish which harness it's for — Claude
Code, Codex, agy, or other/unknown. Ask if the request doesn't say, unless
the brief is clearly harness-agnostic. This isn't an adaptive "ask only if
open" item; the harness changes the draft. Then read
`references/harness-notes.md` for that harness.

## Question pool

Ask only the items the request leaves genuinely open. Max 4, one round,
each with a recommended default.

1. **Goal & done-criteria** — what should exist or behave differently
   when the task is finished? What is the observable "done"?
2. **Task archetype** — feature build, incident forensics, bugfix/repro,
   code review/audit, refactor/migration, or frontend/UI?
3. **Files / modules in scope** — which parts of the codebase are
   involved? Can the agent read the existing code, or is this greenfield?
4. **Constraints** — language, framework, style conventions; what must
   *not* change (public APIs, schemas, dependencies); performance or
   compatibility requirements.
5. **Scope ceiling** — minimal change vs. "above and beyond"? Should
   unrequested refactors, cleanup, extra markdown files, or new abstractions
   be explicitly barred?
6. **Verification** — how does the agent confirm it worked? Existing test
   suite, a new test, a build, a manual check, a script to run?
7. **Action stance (Directives vs. Inquiries)** — implement directly, or investigate and propose a
   plan first for review (explore → plan → execute)? (*Harness note for agy / Gemini CLI:* Gemini models
   assume all turns are read-only Inquiries unless prompted with unambiguous imperative verbs like `implement`, `fix`, or `modify`;
   write explicit action directives and done criteria to avoid the agent stalling in advisory mode.)
8. **Tool boundaries & environment capabilities** — raw bash vs dedicated harness tools? Are there specific skills, plugins, or MCP servers installed in the environment that the agent should leverage? (Run `./tools/token_audit.py env` to discover active capabilities like browser automation, specialized documentation MCPs, or framework skills.)

(Target harness is resolved before this pool, not inside it — see above.)

## Base Template (Feature / Implementation)

```markdown
<role>
You are an autonomous engineer working in <project / stack>. <One line on what the codebase is.>
</role>

<context>
<Relevant background: where code lives, build/test tooling, domain invariants.
Point at files rather than pasting them unless short.
Keep static invariants here at the top to preserve prompt cache prefixes.>

<!-- Optional: Discovered environment capabilities (from `tools/token_audit.py env`) -->
<available_environment_capabilities>
- Skills: `<e.g. ratatui, chrome-devtools>`
- MCP Servers: `<e.g. gemini-api-docs, cloudflare-docs>`
</available_environment_capabilities>
</context>

<task>
<The goal in 1–2 sentences, as an active instruction: "Add…", "Implement…".
Then the observable done-criteria as a numbered list.>
1. <observable outcome 1>
2. <observable outcome 2>
</task>

<constraints>
- Stay within <files / modules>. Do not touch <out-of-scope areas>.
- Tool boundaries: Use dedicated file-reading/editing tools over raw shell redirection (`cat > file`) to allow harness staleness checks.
- Anti-slurp: Inspect files with targeted line bounds and bounded tools (`rg -n -C 1`, `git diff --stat`). Never dump whole files >150 lines.
- Surgical diffs: Apply minimal targeted edits or unified diffs; never echo back unchanged code blocks.
- Do not refactor unrelated code, add unnecessary abstractions, or create
  unprompted documentation/scratch files in the repo root.
- Implement a general solution; do not hardcode logic to pass test fixtures.
- Match existing code conventions, naming, and error handling.
- Confirm before destructive or hard-to-reverse actions (deleting files,
  force-pushing, dropping data).
- Compaction resilience: Your context window will be automatically compacted
  as it approaches its limit. Do not stop tasks early due to token budget concerns;
  checkpoint state and continue until done.
</constraints>

<verification>
<How to prove it works: "run `<test command>` and confirm it passes",
"build with `<cmd>`". Instruct the agent to run this and iterate on output.>
</verification>

<output>
<What you want back: summary of changes, diff/files touched, test outcomes. Do not echo full unmodified files.>
</output>
```

---

## Specialized Archetypes

### 1. Incident Forensics & Root-Cause Investigation
Use when diagnosing system failures, broken access, data anomalies, or outages without making things worse. Incorporates DeepMind's Step-Back Prompting for root-cause diagnosis.

```markdown
<role>
You are an incident forensics engineer and systems investigator. Your role is evidence-gathering, hypothesis testing, and blast-radius analysis. You are in read-only investigation mode.
</role>

<context>
<Incident timeline, symptoms observed, and prior hypotheses. Clearly distinguish verified facts from working theories. Note environment gotchas (tool aliases, dangerous commands).>
</context>

<task>
Investigate the incident and produce a findings report addressing:
1. Step-back analysis: First state the underlying architectural invariants and known failure modes of <subsystem> (e.g., connection pool lifecycle, state reconciliation in distributed workers, permission boundaries).
2. Root-cause mechanism: Trace the exact chain of events that triggered the unexpected state change. Verify with file timestamps and audit logs.
3. Blast radius: What accounts, services, credentials, or data were modified, exposed, or destroyed?
4. Current state verification: Is the system currently secure, stable, and accessible?
5. Recommended remediation: Propose minimal, targeted recovery steps (do not apply them yet).
</task>

<constraints>
- STRICTLY READ-ONLY. Do not modify files, restart services, alter permissions, or run destructive commands.
- Anti-slurp: Filter log searches (`rg -n`, `journalctl -n 50`, `head/tail`); never dump unconstrained logs exceeding 100 lines into context.
- Verify assumptions against logs, file timestamps, audit trails, and command histories before drawing conclusions.
- If you notice unexpected state, record it explicitly rather than attempting an inline fix.
</constraints>

<output>
Present findings first: Timeline -> Root Cause -> Evidence / Citations -> Blast Radius -> Proposed Remediation.
</output>
```

### 2. Bugfix & Regression Isolation
Use when fixing a reported defect with zero collateral damage.

```markdown
<role>
You are a software engineer diagnosing and fixing a bug in <project>.
</role>

<context>
<Error logs, stack trace, user report, or failing scenario. Point to relevant modules.>
</context>

<task>
Fix the bug where <symptom occurs under condition>.
1. First, locate the root cause in <suspected files>.
2. Reproduce the bug by writing a targeted test case that fails.
3. Apply the minimal correct fix to make the test pass.
4. Verify the existing test suite still passes without regression.
</task>

<constraints>
- Minimal diff: fix the root cause without refactoring surrounding code or altering public API signatures.
- Anti-slurp: Inspect suspected files using targeted line bounds; never dump full files.
- Thinking damping: Commit to the first direct, verifiable root-cause fix. Avoid evaluating divergent architectural paradigms.
- Do not add broad try/catch blocks or silent fallbacks that swallow errors.
- Ensure the fix solves the general problem, not just the isolated repro case.
</constraints>

<verification>
Run `<test command>` to confirm the new regression test passes and all existing tests succeed.
</verification>
```

### 3. Code Review & Security Audit
Use when inspecting PRs, code diffs, or existing packages for risks.

```markdown
<role>
You are a senior security engineer and code reviewer performing a thorough audit.
</role>

<context>
<Diff, branch, or module in scope. Target environment, privilege level, and threat model.>
</context>

<task>
Review <target> for security vulnerabilities, logic bugs, data races, edge-case failures, and architectural regressions.
</task>

<constraints>
- Findings-first: Present issues ordered by severity (Critical -> High -> Medium -> Low -> Informational).
- For every finding, include:
  * File and line number reference.
  * Concrete failure scenario / exploit mechanism.
  * Direct remediation recommendation with snippet.
- If no critical issues are found, explicitly state remaining risks and testing gaps.
- Keep introductory summaries brief; do not bury findings behind long recaps.
</constraints>

<output>
1. Severity-ordered findings list.
2. Residual risks & test coverage gaps.
3. Summary verdict (Approve / Request Changes).
</output>
```

### 4. Refactoring & Architecture Migration (Phased)
Use when restructuring code, migrating dependencies, or rewriting modules safely.

```markdown
<role>
You are a staff engineer leading a clean refactoring of <module>.
</role>

<context>
<Current architecture, desired target state, and motivation for the refactor.>
</context>

<task>
Refactor <module> in three strict phases:

Phase 1 (Explore): Inspect existing callers, interfaces, and test coverage. Report all touchpoints and potential behavioral divergence. Do not edit code.
Phase 2 (Plan): Write a detailed implementation plan artifact (files to modify, dependency changes, step-by-step migration sequence). Stop and wait for my approval.
Phase 3 (Execute): Once approved, apply edits incrementally. Run verification between steps.
</task>

<constraints>
- Preserve all external public contracts, wire formats, and runtime behaviors unless explicitly specified.
- Do not introduce new third-party dependencies without prior consent.
- Keep git commits or checkpoints atomic per sub-step.
</constraints>

<verification>
Run `<build command>` and `<test command>` after each logical step. All existing tests must remain green.
</verification>
```

### 5. Frontend & UI Implementation
Use for web/desktop UI, design system components, or responsive layout tasks.

```markdown
<role>
You are a frontend engineer and UI specialist working in <framework / design system>.
</role>

<context>
<Component library, CSS/styling framework, color tokens, typography, and existing UI conventions.>
</context>

<task>
Implement <component/screen>.
1. Build the component matching <design spec / mockup>.
2. Implement all interactive states: default, hover, active, focus-visible, disabled, loading, empty, and error.
3. Ensure full responsive adaptation for mobile, tablet, and desktop breakpoints.
4. Verify accessibility: semantic HTML, ARIA attributes where needed, keyboard navigation, and color contrast.
</task>

<constraints>
- Match existing design system tokens and typography; avoid generic "AI template" styles or arbitrary hardcoded hex colors.
- Use realistic domain data in previews/mocks, not "Lorem Ipsum".
- Do not install new UI libraries or icon sets if existing repo utilities cover them.
</constraints>

<verification>
Run `<lint/typecheck>` and `<component test / storybook / dev server check>`.
</verification>
```
