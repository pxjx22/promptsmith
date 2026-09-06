#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "tiktoken>=0.7.0",
# ]
# ///
"""
Token Audit & Benchmarking Tool for Promptsmith
Measures token counts, session context taxes, prompt caching prefix hygiene,
and guardrails (anti-slurp, diff output, thinking damping) across agent prompts.
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


def analyze_hygiene(content: str) -> dict:
    """Analyze context hygiene, anti-slurp bounds, and caching indicators."""
    lower = content.lower()
    
    # 1. Anti-slurp checks (bounds on tool output)
    has_anti_slurp = any(kw in lower for kw in [
        "anti-slurp", "line ranges", "line limit", "bounded", "do not cat", 
        "never dump whole", "stay within", "rg -n", "head", "tail", "exceeding 200 lines"
    ])
    
    # 2. Diff-first / surgical output checks
    has_diff_contract = any(kw in lower for kw in [
        "diff", "patch", "minimal diff", "surgical", "apply_patch", "unified diff"
    ])
    
    # 3. Thinking / verbosity damping
    has_thinking_damping = any(kw in lower for kw in [
        "damping", "overthinking", "concise", "be direct", "commit to the first", "effort"
    ])
    
    # 4. Prompt caching prefix cleanliness (does it put dynamic timestamps at the very head?)
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

    return {
        "anti_slurp": has_anti_slurp,
        "diff_contract": has_diff_contract,
        "thinking_damping": has_thinking_damping,
        "cache_warning": cache_warning,
        "constraints_count": constraints_count,
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
                "references/harness-notes.md", "references/repo-rules.md"
            ] if os.path.exists(os.path.join(repo_root, f))
        ]
        paths = sorted(default_prompts) + repo_files

    if not paths:
        print("No files found to audit.")
        return

    print("=" * 105)
    print(f"{'Target / File':<42} | {'cl100k':<7} | {'o200k':<7} | {'20-Turn Tax':<11} | {'Slurp':<6} | {'Diff':<5} | {'Damp':<5} | {'Cache'}")
    print("=" * 105)

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
        h = analyze_hygiene(content)

        slurp_icon = "✓" if h["anti_slurp"] else "✗"
        diff_icon = "✓" if h["diff_contract"] else "✗"
        damp_icon = "✓" if h["thinking_damping"] else "—"
        cache_icon = "WARN" if h["cache_warning"] else "✓"

        rel_name = os.path.basename(path)
        if "promptsmith" in path:
            rel_name = "promptsmith/" + os.path.basename(path)

        print(f"{rel_name:<42} | {cl:<7} | {o:<7} | {tax_20:<11,d} | {slurp_icon:<6} | {diff_icon:<5} | {damp_icon:<5} | {cache_icon}")

    print("=" * 105)
    print(f"Total audited files: {len(paths)} | Total cl100k tokens: {total_cl:,} | Total o200k tokens: {total_o:,}")
    print("\nLegend:")
    print("  - 20-Turn Tax: Estimated cumulative input tokens consumed if this prompt persists in session history for 20 turns.")
    print("  - Slurp: [✓] Contains anti-slurp directives (line limits, bounded tool calls). [✗] Risk of context blowup.")
    print("  - Diff:  [✓] Contains diff-first / surgical patch output contract. [✗] Risk of full-file echoes.")
    print("  - Damp:  [✓] Contains thinking/verbosity damping. [—] Standard reasoning.")
    print("  - Cache: [✓] Static prefix stable. [WARN] Dynamic timestamps in header may invalidate KV cache.")


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

    h1 = analyze_hygiene(c1)
    h2 = analyze_hygiene(c2)

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
    print(f"  Anti-slurp bounds:   [{'✓' if h1['anti_slurp'] else '✗'}] -> [{'✓' if h2['anti_slurp'] else '✗'}]")
    print(f"  Diff-first contract: [{'✓' if h1['diff_contract'] else '✗'}] -> [{'✓' if h2['diff_contract'] else '✗'}]")
    print(f"  Thinking damping:    [{'✓' if h1['thinking_damping'] else '✗'}] -> [{'✓' if h2['thinking_damping'] else '✗'}]")
    print(f"  Constraint bullets:  {h1['constraints_count']} in original vs {h2['constraints_count']} in compressed")

    if h1["constraints_count"] > 0 and h2["constraints_count"] < h1["constraints_count"] // 2:
        print("\n  ⚠️  WARNING: Compressed version dropped more than 50% of constraint bullets!")
        print("      Check for missing safety invariants.")
    print("=" * 60)


def cmd_tax(args):
    """Calculate cumulative session context tax."""
    tokens = args.tokens
    turns = args.turns
    total = tokens * turns
    print(f"Prompt base tokens: {tokens:,}")
    print(f"Session turn depth: {turns} turns")
    print(f"Cumulative context tax: {total:,} input tokens across session")
    cost_uncached = (total / 1_000_000) * 3.0
    cost_cached = (total / 1_000_000) * 0.30
    print(f"Estimated re-reading cost (uncached): ~${cost_uncached:.4f}")
    print(f"Estimated re-reading cost (cached):   ~${cost_cached:.4f} (90% cache discount)")


def main():
    parser = argparse.ArgumentParser(description="Promptsmith Token Audit & Benchmarking Utility")
    subparsers = parser.add_subparsers(dest="command")

    p_audit = subparsers.add_parser("audit", help="Audit token sizes and hygiene of prompts or references")
    p_audit.add_argument("files", nargs="*", help="Files or glob patterns to audit (default: ~/prompts/*.md and Promptsmith)")

    p_comp = subparsers.add_parser("compare", help="Compare original vs compressed prompt")
    p_comp.add_argument("orig", help="Path to original prompt")
    p_comp.add_argument("comp", help="Path to compressed prompt")

    p_tax = subparsers.add_parser("tax", help="Calculate session context tax for a token size")
    p_tax.add_argument("tokens", type=int, help="Number of tokens in prompt")
    p_tax.add_argument("--turns", type=int, default=20, help="Number of session turns (default: 20)")

    args = parser.parse_args()

    if args.command == "audit" or args.command is None:
        cmd_audit(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "tax":
        cmd_tax(args)


if __name__ == "__main__":
    main()
