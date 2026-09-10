#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "tiktoken>=0.7.0",
# ]
# ///
"""
Token Audit & Benchmarking Tool for Promptsmith (v2.2.0)
Measures token counts, session context taxes, prompt caching prefix hygiene,
and guardrails (anti-slurp, diff output, thinking damping) across agent prompts.
Includes Anthropic 2026 Prompt Cruft Auditing (pressure language, obsolete scaffolds).
"""

import argparse
import glob
import os
import re
import sys

try:
    import tiktoken
    ENC_CL100K = tiktoken.get_encoding("cl100k_base")
    ENC_O200K = tiktoken.get_encoding("o200k_base")
except ImportError:
    print("Error: tiktoken is not installed. Run with `uv run tools/token_audit.py` or `pip install tiktoken`.")
    sys.exit(1)


def count_tokens(text: str) -> tuple[int, int]:
    """Returns (cl100k_tokens, o200k_tokens)."""
    return len(ENC_CL100K.encode(text)), len(ENC_O200K.encode(text))


def is_reference_or_negative_callout(line: str) -> bool:
    """
    Distinguish actual prompt instructions from reference documentation citations,
    markdown tables (|), headings (#), blockquotes (>), negative-example callouts,
    and meta-guidelines prescribing the elimination of anti-patterns.
    """
    line_s = line.strip()
    if not line_s:
        return True

    # 1. Markdown tables (| col | col |)
    if line_s.startswith("|"):
        return True

    # 2. Markdown headings (# Heading)
    if line_s.startswith("#"):
        return True

    # 3. Blockquotes (> quote)
    if line_s.startswith(">"):
        return True

    # 4. Explicit negative-example callouts
    if re.match(
        r"^(\s*[-*]|\d+\.)?\s*\*{0,2}(weak|bad|anti-pattern|negative|avoid|instead of)\*{0,2}:",
        line_s,
        re.IGNORECASE,
    ):
        return True

    # 5. Rubric evaluation questions / checklist items
    if re.match(
        r"^(\s*[-*]|\d+\.)?\s*(is|are)\s+.*\b(stripped|replaced|eliminated|removed|avoided)\b",
        line_s,
        re.IGNORECASE,
    ):
        return True

    # 6. Meta-documentation prescribing removal, de-escalation, or avoidance of patterns
    meta_patterns = [
        r"\b(strip|stripping|stripped)\b.*\b(pressure language|scaffolds?|shouted|caps)\b",
        r"\b(retire|retiring|retired)\b.*\b(scaffolds?|incantations?)\b",
        r"\b(eliminate|eliminating|delete|deleting|remove|removing|omit|omitting)\b.*\b(shouted|scaffolds?|incantations?|pressure language)\b",
        r"\b(de-escalate|deescalate)\b",
        r"\bpressure language neutralization\b",
        r"\bscaffold replacement\b",
        r"\bdo not use\s+[`\"'].*[`\"']",
        r"\bnever prompt\b.*\bwith\b",
        r"\bdeprecated models?.*should never be targeted\b",
        r"^\s*[-*]\s*\*\*omit pressure language:\*\*",
        r"^\s*[-*]\s*rule:\s*never prompt\b",
    ]
    for mp in meta_patterns:
        if re.search(mp, line_s, re.IGNORECASE):
            return True

    return False


def find_cruft(content: str, filename: str = "") -> list[dict]:
    """
    Find specific dated instructions, pressure language, and obsolete scaffolds
    based on the Anthropic 2026 Prompt Audit methodology.
    Distinguishes actual prompt instructions from reference documentation citations,
    markdown tables, negative examples, and code blocks.
    """
    findings = []
    lines = content.splitlines()

    # 1. Frontmatter cache invalidation (timestamps in header)
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:20], start=2):
            if line.strip() == "---":
                break
            if re.search(r"created:\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", line, re.IGNORECASE):
                findings.append({
                    "file": filename,
                    "line": i,
                    "text": line.strip(),
                    "pattern": "Dynamic timestamp in prefix",
                    "why": "Breaks KV cache prefix invariance across runs; invalidates cached prompt tokens",
                    "confidence": "High",
                    "action": "remove / keep date only (YYYY-MM-DD)",
                })

    # Patterns for body scanning
    caps_pressure_re = re.compile(r"\b(CRITICAL|MUST|NEVER|ALWAYS)\b")
    excl_re = re.compile(r"!{2,}")
    trait_re = re.compile(r"\b(you have a tendency to|do not be lazy|be thorough)\b", re.IGNORECASE)

    scaffold_patterns = [
        (re.compile(r"\bthink step by step\b", re.IGNORECASE), "Dated chain-of-thought prompt incantation", 'Use native thinking: {type: "adaptive"} + effort; incantation is redundant'),
        (re.compile(r"<\/?(scratchpad|thinking)>", re.IGNORECASE), "Obsolete manual scratchpad tag", "Native reasoning replaces manual scratchpads"),
        (re.compile(r"\boutput ONLY valid JSON\b", re.IGNORECASE), "Dated pre-structured-outputs JSON forcing", "Use structured outputs (output_config.format)"),
        (re.compile(r"\bevery \d+ (tool calls|messages)\b", re.IGNORECASE), "Rigid update cadence choreography", "Delete; modern models narrate appropriately"),
        (re.compile(r"\bat most \d+ (words|sentences)\b", re.IGNORECASE), "Numeric output ceiling", "Use qualitative guidance ('be concise') to avoid reasoning starvation"),
        (re.compile(r"\bjson\.loads inside retry\b", re.IGNORECASE), "JSON retry parsing scaffold", "Replace with API-native Structured Outputs"),
        (re.compile(r"\bgemini-(1\.5|2\.0|2\.5|3\.0)\b", re.IGNORECASE), "Deprecated Gemini model string", "Upgrade to gemini-3.8-flash, gemini-3.5-flash-lite, or gemini-3.1-pro-preview"),
        (re.compile(r"\b(google\.generativeai|@google\/generative-ai)\b", re.IGNORECASE), "Deprecated legacy Gemini SDK package", "Migrate to google-genai or @google/genai"),
        (re.compile(r"\b(generateContent|generate_content)\b"), "Legacy Gemini generateContent API", "Migrate to Interactions API (client.interactions.create)"),
    ]

    in_code_block = False
    for i, line in enumerate(lines):
        line_num = i + 1
        line_s = line.strip()

        if line_s.startswith("```") or line_s.startswith("~~~"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Skip scanning promptsmith documentation headers
        if line_s.startswith(">") and "synthesized from" in line_s:
            continue

        if is_reference_or_negative_callout(line):
            continue

        # Check pressure language
        caps_matches = caps_pressure_re.findall(line)
        if len(caps_matches) >= 2 or excl_re.search(line):
            findings.append({
                "file": filename,
                "line": line_num,
                "text": line_s[:80],
                "pattern": "Pressure Language (shouting caps / !! )",
                "why": "Causes over-triggering, rigid edge cases, and anxious hedging on modern models",
                "confidence": "High",
                "action": "rewrite: state requirement calmly at normal volume with rationale",
            })

        m_trait = trait_re.search(line)
        if m_trait:
            findings.append({
                "file": filename,
                "line": line_num,
                "text": line_s[:80],
                "pattern": f"Trait claim ('{m_trait.group(1)}')",
                "why": "Frontier models are proactive by default; patronizing rules induce over-caution",
                "confidence": "Medium",
                "action": "remove / state affirmative task requirement directly",
            })

        # Check obsolete scaffolds
        for pat, desc, fix in scaffold_patterns:
            if pat.search(line):
                findings.append({
                    "file": filename,
                    "line": line_num,
                    "text": line_s[:80],
                    "pattern": desc,
                    "why": "Replaced by native API features; manual scaffolds degrade output quality",
                    "confidence": "High",
                    "action": f"replace-with-API-feature: {fix}",
                })

    return findings


def analyze_hygiene(content: str, filename: str = "") -> dict:
    """Analyze context hygiene, anti-slurp bounds, caching, and cruft indicators."""
    lower = content.lower()
    
    # 1. Anti-slurp & ACI stream filtering checks (SWE-agent / Princeton)
    has_anti_slurp = any(kw in lower for kw in [
        "anti-slurp", "line ranges", "line limit", "bounded", "do not cat", 
        "never dump whole", "stay within", "rg -n", "head", "tail", "exceeding", "max-count"
    ])
    has_aci_stream = any(kw in lower for kw in [
        "| head", "| tail", "max-count", "diff --stat", "no-pager", "-n 25", "-n 30", "-n 50"
    ])
    
    # 2. Diff-first / surgical output checks
    has_diff_contract = any(kw in lower for kw in [
        "diff", "patch", "minimal diff", "surgical", "apply_patch", "unified diff"
    ])
    
    # 3. Thinking / verbosity damping (Snell et al. / DeepMind)
    has_thinking_damping = any(kw in lower for kw in [
        "damping", "overthinking", "concise", "be direct", "commit to the first", "effort"
    ])
    
    # 4. Prompt caching prefix cleanliness (TokenPilot / arXiv:2606.17016)
    cache_warning = False
    lines = content.strip().splitlines()
    if lines and lines[0].strip() == "---":
        fm = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            fm.append(line.lower())
        fm_text = "\n".join(fm)
        if re.search(r"created:\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", fm_text):
            cache_warning = True

    # 5. Extract constraints count if XML tag exists
    constraints_match = re.search(r"<constraints>(.*?)</constraints>", content, re.DOTALL | re.IGNORECASE)
    constraints_count = 0
    if constraints_match:
        c_body = constraints_match.group(1).strip()
        constraints_count = len([l for l in c_body.splitlines() if l.strip().startswith(("-", "*", "1", "2", "3", "4", "5"))])

    # 6. Cruft analysis (Anthropic 2026)
    cruft_items = find_cruft(content, filename=filename)

    return {
        "anti_slurp": has_anti_slurp,
        "aci_stream": has_aci_stream,
        "diff_contract": has_diff_contract,
        "thinking_damping": has_thinking_damping,
        "cache_warning": cache_warning,
        "constraints_count": constraints_count,
        "cruft_count": len(cruft_items),
        "cruft_items": cruft_items,
    }


def cmd_audit(args):
    paths = []
    if args.files:
        for p in args.files:
            matches = glob.glob(os.path.expanduser(p))
            if matches:
                paths.extend(matches)
            elif os.path.exists(p):
                paths.append(p)
    else:
        default_prompts = glob.glob(os.path.expanduser("~/prompts/*.md"))
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        repo_files = [
            os.path.join(repo_root, f) for f in [
                "SKILL.md", "references/best-practices.md", "references/coding-agent-brief.md",
                "references/harness-notes.md", "references/repo-rules.md", "references/general-llm-prompt.md"
            ] if os.path.exists(os.path.join(repo_root, f))
        ]
        paths = sorted(default_prompts) + repo_files

    if not paths:
        print("No files found to audit.")
        return

    print("=" * 115)
    print(f"{'Target / File':<38} | {'cl100k':<7} | {'o200k':<7} | {'20-Turn Tax':<11} | {'Slurp':<6} | {'Diff':<5} | {'Damp':<5} | {'Cruft':<6} | {'Cache'}")
    print("=" * 115)

    total_cl = 0
    total_o = 0

    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Could not read {path}: {e}")
            continue

        cl, o = count_tokens(content)
        total_cl += cl
        total_o += o
        tax_20 = cl * 20
        h = analyze_hygiene(content, filename=path)

        slurp_icon = "✓" if h["anti_slurp"] else "✗"
        diff_icon = "✓" if h["diff_contract"] else "✗"
        damp_icon = "✓" if h["thinking_damping"] else "—"
        cache_icon = "WARN" if h["cache_warning"] else "✓"
        cruft_icon = f"WARN({h['cruft_count']})" if h["cruft_count"] > 0 else "✓"

        rel_name = os.path.basename(path)
        if "promptsmith" in path:
            rel_name = "promptsmith/" + os.path.basename(path)

        print(f"{rel_name:<38} | {cl:<7} | {o:<7} | {tax_20:<11,d} | {slurp_icon:<6} | {diff_icon:<5} | {damp_icon:<5} | {cruft_icon:<6} | {cache_icon}")

    print("=" * 115)
    print(f"Total audited files: {len(paths)} | Total cl100k tokens: {total_cl:,} | Total o200k tokens: {total_o:,}")
    print("\nLegend:")
    print("  - 20-Turn Tax: Estimated cumulative input tokens consumed if this prompt persists in session history for 20 turns.")
    print("  - Slurp: [✓] Contains anti-slurp directives (line limits, bounded tool calls). [✗] Risk of context blowup.")
    print("  - Diff:  [✓] Contains diff-first / surgical patch output contract. [✗] Risk of full-file echoes.")
    print("  - Damp:  [✓] Contains thinking/verbosity damping. [—] Standard reasoning.")
    print("  - Cruft: [✓] Clean. [WARN(N)] N dated instructions, pressure words, or obsolete scaffolds detected (run `cruft` command).")
    print("  - Cache: [✓] Static prefix stable. [WARN] Dynamic timestamps in header may invalidate KV cache.")


def cmd_cruft(args):
    """Detailed Anthropic 2026 Cruft Audit for target prompt files."""
    paths = []
    for p in args.files:
        matches = glob.glob(os.path.expanduser(p))
        if matches:
            paths.extend(matches)
        elif os.path.exists(p):
            paths.append(p)

    if not paths:
        print("Please specify one or more files to inspect for cruft.")
        return

    print("=" * 90)
    print("PROMPT CRUFT AUDIT REPORT (Anthropic 2026 Methodology)")
    print("Prime Directive: Distinguish cruft from load-bearing content. Context is never cruft.")
    print("=" * 90)

    total_findings = 0
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {path}: {e}")
            continue

        findings = find_cruft(content, filename=path)
        total_findings += len(findings)

        print(f"\nTarget: {path}")
        if not findings:
            print("  ✓ Clean! No dated scaffolds, pressure shouting, or prefix invalidators found.")
            continue

        print(f"  Found {len(findings)} potential cruft items:\n")
        for idx, item in enumerate(findings, start=1):
            print(f"  [{idx}] Line {item['line']}: {item['pattern']} ({item['confidence']} Confidence)")
            print(f"      Evidence: \"{item['text']}\"")
            print(f"      Why:      {item['why']}")
            print(f"      Action:   {item['action']}")
            print()

    print("=" * 90)
    print(f"Audit complete. Total findings across {len(paths)} file(s): {total_findings}")


def cmd_compare(args):
    """Compare an original prompt vs a compressed prompt."""
    file1, file2 = args.orig, args.comp
    for p in [file1, file2]:
        if not os.path.exists(p):
            print(f"Error: File does not exist: {p}")
            return

    with open(file1, "r", encoding="utf-8") as f:
        c1 = f.read()
    with open(file2, "r", encoding="utf-8") as f:
        c2 = f.read()

    cl1, o1 = count_tokens(c1)
    cl2, o2 = count_tokens(c2)

    delta_cl = cl2 - cl1
    pct_cl = (delta_cl / cl1) * 100 if cl1 > 0 else 0
    delta_o = o2 - o1
    pct_o = (delta_o / o1) * 100 if o1 > 0 else 0

    tax1_20 = cl1 * 20
    tax2_20 = cl2 * 20
    savings_20 = tax1_20 - tax2_20

    h1 = analyze_hygiene(c1, filename=file1)
    h2 = analyze_hygiene(c2, filename=file2)

    print("\n" + "=" * 60)
    print(f"PROMPT COMPRESSION COMPARISON")
    print("=" * 60)
    print(f"Original:   {file1}")
    print(f"Compressed: {file2}")
    print("-" * 60)
    print(f"Metric               Original      Compressed     Delta")
    print(f"cl100k tokens:       {cl1:<13} {cl2:<14} {delta_cl:+d} ({pct_cl:+.1f}%)")
    print(f"o200k tokens:        {o1:<13} {o2:<14} {delta_o:+d} ({pct_o:+.1f}%)")
    print(f"20-Turn Tax:         {tax1_20:<13,d} {tax2_20:<14,d} -{savings_20:,d} tokens")
    print("-" * 60)
    print("HYGIENE & GUARDRAIL RETENTION:")
    s1 = "✓" if h1["anti_slurp"] else "✗"
    s2 = "✓" if h2["anti_slurp"] else "✗"
    a1 = "✓" if h1["aci_stream"] else "✗"
    a2 = "✓" if h2["aci_stream"] else "✗"
    d1 = "✓" if h1["diff_contract"] else "✗"
    d2 = "✓" if h2["diff_contract"] else "✗"
    t1 = "✓" if h1["thinking_damping"] else "—"
    t2 = "✓" if h2["thinking_damping"] else "—"
    cruft_delta = h2["cruft_count"] - h1["cruft_count"]
    print(f"  Anti-slurp bounds:   [{s1}] -> [{s2}]")
    print(f"  ACI stream filter:   [{a1}] -> [{a2}]")
    print(f"  Diff-first contract: [{d1}] -> [{d2}]")
    print(f"  Thinking damping:    [{t1}] -> [{t2}]")
    print(f"  Cruft items:         {h1['cruft_count']} in orig -> {h2['cruft_count']} in comp (delta: {cruft_delta})")
    print(f"  Constraint bullets:  {h1['constraints_count']} in original vs {h2['constraints_count']} in compressed")

    if h1["constraints_count"] > 0 and h2["constraints_count"] < h1["constraints_count"] // 2:
        print("\n  ⚠️  WARNING: Compressed version dropped more than 50% of constraint bullets!")
        print("      Check for missing safety invariants.")
    print("=" * 60)


def cmd_tax(args):
    """Calculate cumulative session context tax and fracture zone threshold."""
    tokens = args.tokens
    turns = args.turns
    total = tokens * turns
    print(f"Prompt base tokens:     {tokens:,}")
    print(f"Session turn depth:     {turns} turns")
    print(f"Cumulative context tax: {total:,} input tokens across session")
    cost_uncached = (total / 1_000_000) * 3.0
    cost_cached = (total / 1_000_000) * 0.30
    print(f"Estimated reading cost (uncached): ~${cost_uncached:.4f}")
    print(f"Estimated reading cost (cached):   ~${cost_cached:.4f} (90% cache discount)")
    
    # 200k Claude window reference & 60% fracture zone
    claude_headroom = 200_000
    utilization_200k = (total / claude_headroom) * 100
    status = "⚠️  Enters 60%–70% fracture zone! Compact proactively." if utilization_200k >= 60 else "✓  Within healthy attention threshold (<60%)."
    print(f"200k Context Consumption:          {utilization_200k:.1f}% ({status})")


def generate_prompt(mode: str, intent: str, target_model: str = "agy (Antigravity 2.0 / Gemini 3.8)") -> str:
    """Generate a valid, frontmattered prompt adhering to the 7-pillar rubric."""
    import datetime
    today = datetime.date.today().strftime("%Y-%m-%d")

    norm_mode = mode.lower().strip()
    if norm_mode in ("brief", "coding-agent-brief", "coding"):
        canonical_mode = "coding-agent-brief"
    elif norm_mode in ("rules", "repo-rules"):
        canonical_mode = "repo-rules"
    elif norm_mode in ("general", "general-llm-prompt"):
        canonical_mode = "general-llm-prompt"
    elif norm_mode in ("compress", "prompt-compressor"):
        canonical_mode = "prompt-compressor"
    else:
        canonical_mode = "coding-agent-brief"

    if canonical_mode == "coding-agent-brief":
        return f"""---
created: {today}
mode: coding-agent-brief
target_model: {target_model}
intent: {intent}
---

<role>
You are an autonomous senior software engineer working in this codebase.
</role>

<context>
Target codebase: Current workspace
Task context: {intent}
Keep static invariants here at the top to preserve prompt cache prefixes.
</context>

<task>
{intent}

Observable Done Criteria:
1. Implement the requested changes addressing the core intent cleanly.
2. Ensure full test coverage and passing verification checks.
3. Keep changes minimal, preserve existing conventions, and maintain backward compatibility.
</task>

<constraints>
- Scope ceiling: Confine modifications strictly to files and modules in scope. Do not refactor unrelated code.
- Anti-slurp: Inspect files with targeted line bounds (`rg -n -C 1`, `git diff --stat`). Never dump whole files >150 lines.
- Surgical diffs: Apply minimal targeted edits or unified diffs; never echo back unchanged code blocks.
- Tool boundaries: Use dedicated file-reading/editing tools over raw shell redirection (`cat > file`) to allow harness staleness checks.
- Harness Directives Mandate: Treat this brief as an imperative Directive; proceed directly to exploration, plan artifact generation, and implementation.
- Post-edit silence: After code modifications, run tests silently without echoing verbose test suite logs or full file contents.
</constraints>

<verification>
Run verification commands and confirm clean exit code 0:
1. Run existing test suite for modified components.
2. Verify linting, formatting, and static analysis checks pass without errors.
</verification>

<output>
Provide a concise summary of changes, surgical diff of modifications, and verification test outcomes. Do not echo full unmodified files.
</output>
"""

    elif canonical_mode == "repo-rules":
        return f"""---
created: {today}
mode: repo-rules
target_model: {target_model}
intent: {intent}
---

<role>
You are an autonomous engineering assistant operating within this repository.
</role>

<context>
Repository context: {intent}
Standards: Modern, minimal, well-tested production patterns.
Preserve static repository guidelines at the root to maintain prompt cache prefix invariance.
</context>

<guidelines>
1. Code Style: Follow idiomatic conventions and maintain consistent architecture.
2. Safety Invariants: Never break existing public APIs or introduce security regressions.
3. Minimal Footprint: Prefer surgical edits over sprawling rewrites.
</guidelines>

<constraints>
- Anti-slurp: Bounded inspections only (`rg -n -C 1`, line limits). Never dump whole files >150 lines.
- Surgical diffs: Produce minimal unified diffs; never echo unchanged code blocks.
- Verification: Always run local test commands before reporting completion.
- Post-edit silence: Execute test verification quietly without verbose full-file dumps.
</constraints>

<verification>
Run local test and lint checks to confirm clean exit status:
1. Test command: Run relevant project tests.
2. Lint command: Verify zero lint and type errors.
</verification>
"""

    elif canonical_mode == "general-llm-prompt":
        return f"""---
created: {today}
mode: general-llm-prompt
target_model: {target_model}
intent: {intent}
---

<context>
Task context: {intent}
Keep background facts and reference material here at the top for prompt cache stability.
</context>

<instructions>
Execute the requested objective with precision and structured clarity.

Observable Done Criteria:
1. Address the primary intent directly without conversational fluff.
2. Structure the output according to the defined format delimiters.
3. Validate all outputs against stated constraints.
</instructions>

<constraints>
- Anti-cruft: State requirements calmly with rationale; do not use shouting caps or dated scaffolds.
- Conciseness: Deliver dense, high-signal information without filler phrases.
- Structured output: Adhere strictly to the requested format delimiters.
</constraints>

<output_format>
Present output directly within clean structural delimiters without conversational preamble or hedging.
</output_format>
"""

    elif canonical_mode == "prompt-compressor":
        return f"""---
created: {today}
mode: prompt-compressor
target_model: {target_model}
intent: {intent}
---

<task>
Compress and de-cruft the target prompt while preserving 100% of load-bearing context and constraints.
Target intent: {intent}
</task>

<compression_directives>
1. Cruft Elimination: Strip pressure shouting (`CRITICAL: MUST`), obsolete scaffolds (`think step by step`, `<scratchpad>`), and deprecated model versions.
2. Anti-Slurp & Diff Retention: Preserve bounded file reading directives and diff-first output contracts.
3. Cache Stability: Ensure frontmatter dates use static `YYYY-MM-DD` format (no dynamic timestamps).
4. Load-Bearing Retention: Keep domain rules, audience specifications, and constraint rationales intact.
</compression_directives>

<output_contract>
Output the compressed prompt in a fenced code block followed by a single-line compression summary:
`~<orig> → ~<comp> tokens (-<pct>%), estimated 20-turn context savings: -<tax> tokens`
</output_contract>
"""
    return ""


def cmd_generate(args):
    """Headless CLI prompt generation for CI/CD pipelines and scripts."""
    target_model = getattr(args, "target_model", None) or "agy (Antigravity 2.0 / Gemini 3.8)"
    prompt_text = generate_prompt(mode=args.mode, intent=args.intent, target_model=target_model)
    if getattr(args, "output", None):
        out_path = os.path.expanduser(args.output)
        parent = os.path.dirname(os.path.abspath(out_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        print(f"Generated prompt written to: {out_path}")
    else:
        print(prompt_text, end="")


def cmd_eval(args):
    """Run automated 7-pillar rubric evals, reverse-line parsing, or file evaluations."""
    try:
        from eval_rubrics import run_eval_suite, format_rubric_report
    except ImportError:
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from eval_rubrics import run_eval_suite, format_rubric_report

    if getattr(args, "files", None):
        paths = []
        for p in args.files:
            matches = glob.glob(os.path.expanduser(p))
            if matches:
                paths.extend(matches)
            elif os.path.exists(p):
                paths.append(p)
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                print(format_rubric_report(content, filename=path))
            except Exception as e:
                print(f"Error evaluating {path}: {e}")
    else:
        success = run_eval_suite()
        sys.exit(0 if success else 1)


def main():
    parser = argparse.ArgumentParser(description="Promptsmith Token Audit & Benchmarking Utility")
    subparsers = parser.add_subparsers(dest="command")

    p_audit = subparsers.add_parser("audit", help="Audit token sizes and hygiene of prompts or references")
    p_audit.add_argument("files", nargs="*", help="Files or glob patterns to audit (default: ~/prompts/*.md and Promptsmith)")

    p_cruft = subparsers.add_parser("cruft", help="Inspect prompt files for dated scaffolds, pressure language, and cruft")
    p_cruft.add_argument("files", nargs="+", help="Files to inspect")

    p_comp = subparsers.add_parser("compare", help="Compare original vs compressed prompt")
    p_comp.add_argument("orig", help="Path to original prompt")
    p_comp.add_argument("comp", help="Path to compressed prompt")

    p_tax = subparsers.add_parser("tax", help="Calculate session context tax for a token size")
    p_tax.add_argument("tokens", type=int, help="Number of tokens in prompt")
    p_tax.add_argument("--turns", type=int, default=20, help="Number of session turns (default: 20)")

    p_gen = subparsers.add_parser("generate", help="Generate a valid prompt template programmatically")
    p_gen.add_argument("--mode", default="brief", choices=["brief", "rules", "general", "compress", "coding-agent-brief", "repo-rules", "general-llm-prompt", "prompt-compressor"], help="Prompt mode (default: brief)")
    p_gen.add_argument("--intent", required=True, help="Intent or task description for the prompt")
    p_gen.add_argument("--target-model", default="agy (Antigravity 2.0 / Gemini 3.8)", help="Target model / harness")
    p_gen.add_argument("-o", "--output", help="Optional output file path")

    p_eval = subparsers.add_parser("eval", help="Run automated 7-pillar rubric evals and regression assertions")
    p_eval.add_argument("files", nargs="*", help="Optional prompt files to evaluate against 7-pillar rubric")

    args = parser.parse_args()

    if args.command == "audit" or args.command is None:
        cmd_audit(args)
    elif args.command == "cruft":
        cmd_cruft(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "tax":
        cmd_tax(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "eval":
        cmd_eval(args)


if __name__ == "__main__":
    main()
