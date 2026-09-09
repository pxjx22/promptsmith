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


def find_cruft(content: str, filename: str = "") -> list[dict]:
    """
    Find specific dated instructions, pressure language, and obsolete scaffolds
    based on the Anthropic 2026 Prompt Audit methodology.
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

        if line_s.startswith("```"):
            in_code_block = not in_code_block
            continue

        # Skip scanning promptsmith documentation headers
        if line_s.startswith(">") and "synthesized from" in line_s:
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

    args = parser.parse_args()

    if args.command == "audit" or args.command is None:
        cmd_audit(args)
    elif args.command == "cruft":
        cmd_cruft(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "tax":
        cmd_tax(args)


if __name__ == "__main__":
    main()
