# Promptsmith ⚒️

> **Cross-tool prompt engineering and agent brief authoring skill for Claude Code, OpenAI Codex, and Google Antigravity (AGY).**

Promptsmith is a unified skill that designs, refines, and audits prompts and agent task briefs across frontier AI developer environments. Built on peer-reviewed prompt engineering literature and harness-specific guidance for 2026 frontier models (Anthropic Claude 5 series, OpenAI GPT-5.6 series, and Google Gemini 3.8 / Antigravity 2.0).

---

## ⚡ Highlights

- **Universal Multi-Harness Support**: Works seamlessly as a native skill across:
  - **Claude Code**: `/promptsmith`
  - **OpenAI Codex**: `$promptsmith`
  - **Google Antigravity (AGY)**: `/promptsmith`
- **Literature-Grounded Best Practices**:
  - **Step-Back Abstraction**: Evoking high-level principles before concrete execution (Google DeepMind).
  - **Few-Shot Class Balancing & Permutation**: Eliminating majority-label and recency bias (Berkeley AI Research).
  - **Prefix Hygiene & Prompt Caching**: Structuring static guidelines and system context ahead of dynamic inputs for cache hits.
  - **Compaction & Context Budgeting**: High-density markdown, structured anchor tables, and handoff manifests designed for long-running autonomous workflows.
  - **Anti-Gaming & Subagent Damping**: Rigorous guardrails against superficial test passing, mock-abuse, and runaway agent recursion.
- **Three Core Modes**:
  1. `coding-agent-brief` (Default): Production task briefs for coding agents across 5 specialized archetypes.
  2. `repo-rules`: Authoring and auditing repository instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).
  3. `general-llm-prompt`: Production prompts, strict JSON Schemas, few-shot classifiers, and a 6-pillar critique rubric.

---

## 📦 Quickstart & Installation

### Option 1: Automatic Cross-Tool Install

Clone the repository and run the installer to automatically discover and install Promptsmith into your active AI agent harnesses:

```bash
git clone https://github.com/pxjx22/promptsmith.git
cd promptsmith
./install.sh
```

To force-create directories for all supported harnesses even if they are not yet installed:
```bash
./install.sh --all
```

The installer configures:
- Claude Code: `~/.claude/skills/promptsmith/`
- OpenAI Codex: `~/.codex/skills/promptsmith/`
- Google Antigravity: `~/.gemini/config/skills/promptsmith/` (and legacy mirror `~/.gemini/skills/promptsmith/`)

### Option 2: Manual Installation

Copy the `promptsmith` directory into the skill directory of your target tool:
```bash
# Claude Code
cp -r . ~/.claude/skills/promptsmith

# OpenAI Codex
cp -r . ~/.codex/skills/promptsmith

# Google Antigravity (AGY)
mkdir -p ~/.gemini/config/skills
cp -r . ~/.gemini/config/skills/promptsmith
```

---

## 🚀 Usage

Promptsmith adapts to whether you provide a loose concept, need an existing prompt evaluated, or want a structured agent brief generated.

### 1. In Claude Code
```
/promptsmith "Create a bugfix brief for connection pooling exhaustion in our async worker pool"
/promptsmith "Audit and optimize this extraction prompt for strict JSON Schema output"
```

### 2. In OpenAI Codex
```
$promptsmith "Draft an AGENTS.md file for a Rust microservice with strict lint and clippy rules"
```

### 3. In Google Antigravity (AGY)
```
/promptsmith "Write a forensics brief to diagnose intermittent latency spikes in our gRPC services"
```

Promptsmith will ask clarifying questions if key details (target harness, runtime constraints, verification commands) are missing, then output both an interactive draft and persist a copy to your prompt vault at:
- **Global vault**: `~/prompts/<slug>.md`
- **Project vault**: `./prompts/<slug>.md` (when targeting an active repository)

---

## 🛠️ Modes & Archetypes

### Mode 1: `coding-agent-brief`
Builds task briefs formatted for coding agents executing autonomously. Supports 5 specialized archetypes:
1. **Forensics & Investigation**: Read-only diagnostic loops, root-cause isolation, and hypothesis falsification before touching code.
2. **Bugfix & Reproduction**: Mandatory failing reproduction test, minimal surgical patch, regression test suite, and zero unrelated edits.
3. **Code Review & Audit**: Severity-ranked findings (Critical, High, Medium, Low), concrete reproduction steps, and exact before/after diffs.
4. **Refactor & Migration**: Strangler fig / incremental migration, dual-run / shadow execution, interface parity checks, and instant rollback paths.
5. **Frontend & UI**: Visual specifications, state-matrix coverage (loading, empty, error, active), keyboard navigation, and responsive constraints.

### Mode 2: `repo-rules`
Guides the creation of repository-level agent instruction files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).
- **Core Pillars**: Machine context, hard boundaries, verified build/test commands, code conventions, environment gotchas, and compaction rules.
- **Rule Hygiene**: Filters out trivia the model already knows; strictly documents project-specific quirks, edge cases, and safety barriers.

### Mode 3: `general-llm-prompt`
Designs or evaluates production prompts for application integration:
- **Role & Objective**: High-clarity system framing.
- **Strict JSON Schema Contracts**: Structured output guarantees without parsing errors.
- **Class-Balanced Few-Shot**: Eliminates label skew and ordering bias in classification and extraction tasks.
- **6-Pillar Critique Rubric**: Audits existing prompts against Clarity, Constraint Precision, Example Balance, Error Boundary Handling, Token Economy, and Harness Alignment.

---

## 🧠 Frontier Model Alignment (2026)

Promptsmith includes model-specific calibration notes in [`references/harness-notes.md`](references/harness-notes.md):

| Family | Supported Models | Harness Optimizations |
|---|---|---|
| **Anthropic Claude 5** | Fable 5.1, Opus 5, Sonnet 5 | XML tags (`<context>`, `<instructions>`), prompt caching prefix ordering, thinking budget tuning, negative constraint placement. |
| **OpenAI GPT-5.6** | GPT-5.6 Terra, GPT-5.6 Sol | Markdown headers, strict JSON Schema (`response_format`), explicit tool-call contracts, low-temperature sampling. |
| **Google Gemini / AGY** | Gemini 3.8 Flash, Pro, AGY 2.0 | Explicit system instructions, multi-modal framing, grounded citations, subagent damping controls. |

---

## 📂 Repository Structure

```
promptsmith/
├── SKILL.md                          # Master skill orchestrator & entrypoint
├── install.sh                        # Cross-harness installer and syncer
├── LICENSE                           # MIT License
├── README.md                         # Documentation & usage guide
├── agents/
│   └── openai.yaml                   # Codex agent skill definition
└── references/
    ├── best-practices.md             # Core prompt engineering cheatsheet & research
    ├── coding-agent-brief.md         # Brief templates & the 5 task archetypes
    ├── general-llm-prompt.md         # Application prompt patterns & critique rubric
    ├── repo-rules.md                 # AGENTS.md / CLAUDE.md / GEMINI.md template
    └── harness-notes.md              # Model-specific parameters & nuances
```

---

## 📄 License

[MIT](LICENSE) © 2026 px
