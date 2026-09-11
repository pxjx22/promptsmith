#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "tiktoken>=0.7.0",
# ]
# ///
"""
Automated 7-Pillar Rubric & Eval Harness for Promptsmith (v2.2.0)
Evaluates prompt quality against Promptsmith's 7-pillar rubric, implements
OpenAI Evals cot_classify reverse-line parsing, and runs automated regression tests.
"""

import os
import re
import sys

# Ensure tools directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from token_audit import analyze_hygiene, count_tokens, find_cruft
except ImportError:
    print("Error: token_audit.py not found in path.")
    sys.exit(1)


# ==============================================================================
# 1. The 7-Pillar Rubric Evaluator
# ==============================================================================

def evaluate_rubric(content: str, filename: str = "") -> dict:
    """
    Evaluates a prompt against Promptsmith's 7-Pillar Rubric:
      1. Goal & Done-Criteria
      2. Information Hierarchy & Caching
      3. Positive Framing & Anti-Cruft
      4. Guardrails & Invariants
      5. Grounding & Verification Loop
      6. Target Harness & Tool Surface Alignment
      7. Token Efficiency & Context Hygiene
    """
    lower = content.lower()
    hygiene = analyze_hygiene(content, filename=filename)
    cl_tokens, o_tokens = count_tokens(content)

    pillars = {}

    # Pillar 1: Goal & Done-Criteria
    has_task_tag = bool(re.search(r"<(task|instructions|goal)>", content, re.IGNORECASE))
    has_done_criteria = bool(re.search(
        r"(done criteria|observable done|done:\s*|definition of done|observable outcome|\bcriteria\b|acceptance criteria)",
        lower
    ))
    has_numbered_steps = bool(re.search(r"^\s*1\.\s+", content, re.MULTILINE))
    p1_passed = (has_task_tag or "task" in lower or "goal" in lower) and (has_done_criteria or has_numbered_steps)
    pillars["1_goal_and_done_criteria"] = {
        "passed": p1_passed,
        "detail": "Explicit goal and numbered/observable done criteria defined" if p1_passed else "Missing explicit goal or numbered done criteria"
    }

    # Pillar 2: Information Hierarchy & Caching
    has_xml_delimiters = len(re.findall(r"<\/?(role|context|task|constraints|verification|output|instructions)>", content, re.IGNORECASE)) >= 4
    # Context before task / instructions
    ctx_pos = lower.find("<context>")
    task_pos = lower.find("<task>")
    inst_pos = lower.find("<instructions>")
    target_pos = task_pos if task_pos != -1 else inst_pos
    context_ordered = True if ctx_pos == -1 or target_pos == -1 else (ctx_pos < target_pos)
    cache_clean = not hygiene["cache_warning"]
    p2_passed = has_xml_delimiters and context_ordered and cache_clean
    pillars["2_information_hierarchy_and_caching"] = {
        "passed": p2_passed,
        "detail": "Clean XML structuring, context-first ordering, and stable cache prefix" if p2_passed else "Weak structural delimiters, inverted context ordering, or dynamic timestamps in prefix"
    }

    # Pillar 3: Positive Framing & Anti-Cruft
    cruft_items = hygiene["cruft_items"]
    p3_passed = len(cruft_items) == 0
    pillars["3_positive_framing_and_anti_cruft"] = {
        "passed": p3_passed,
        "detail": "Zero cruft: no shouting caps, no dated CoT scaffolds, calm volume" if p3_passed else f"{len(cruft_items)} cruft item(s) detected (shouting caps, dated scaffolds, or relics)"
    }

    # Pillar 4: Guardrails & Invariants
    has_constraints = bool(re.search(r"<(constraints|guardrails|guidelines)>", content, re.IGNORECASE)) or "constraints:" in lower
    has_scope_bounds = any(kw in lower for kw in ["scope", "stay within", "do not touch", "ceiling", "confine", "do not refactor"])
    p4_passed = has_constraints and (has_scope_bounds or hygiene["constraints_count"] > 0)
    pillars["4_guardrails_and_invariants"] = {
        "passed": p4_passed,
        "detail": "Explicit scope boundaries and invariant constraints defined" if p4_passed else "Missing explicit constraints or scope boundaries"
    }

    # Pillar 5: Grounding & Verification Loop
    has_verif_tag = bool(re.search(r"<(verification|validation|test_plan)>", content, re.IGNORECASE))
    has_verif_commands = any(kw in lower for kw in ["pytest", "test", "cargo test", "npm test", "verify", "run", "exit code 0", "assertion"])
    p5_passed = has_verif_tag or (has_verif_commands and "verify" in lower)
    pillars["5_grounding_and_verification"] = {
        "passed": p5_passed,
        "detail": "Explicit verification commands and exit-code validation specified" if p5_passed else "Missing verification loop and concrete validation steps"
    }

    # Pillar 6: Target Harness & Tool Surface Alignment
    has_harness_alignment = any(kw in lower for kw in [
        "harness", "tool boundaries", "dedicated tool", "staleness", "directive", 
        "sub-agent", "subagent", "claude code", "codex", "agy", "antigravity", "gemini",
        "glm", "glm-5.3", "z.ai", "opencode"
    ])
    p6_passed = has_harness_alignment or bool(re.search(r"target_model:\s*\w+", content))
    pillars["6_target_harness_alignment"] = {
        "passed": p6_passed,
        "detail": "Aligned with target harness tool boundaries and execution stance" if p6_passed else "Generic prompt without harness-specific tool or stance alignment"
    }

    # Pillar 7: Token Efficiency & Context Hygiene
    p7_passed = hygiene["anti_slurp"] and hygiene["diff_contract"]
    pillars["7_token_efficiency_and_hygiene"] = {
        "passed": p7_passed,
        "detail": "Enforces anti-slurp bounded reading and diff-first patch contracts" if p7_passed else "Lacks anti-slurp line bounds or surgical diff-first output contracts"
    }

    score = sum(1 for p in pillars.values() if p["passed"])

    return {
        "score": score,
        "max_score": 7,
        "passed": score >= 6,
        "pillars": pillars,
        "cruft_count": len(cruft_items),
        "cruft_items": cruft_items,
        "hygiene": hygiene,
        "tokens": (cl_tokens, o_tokens),
        "filename": filename,
    }


def format_rubric_report(content: str, filename: str = "") -> str:
    """Formats a visual scorecard for the 7-pillar evaluation."""
    res = evaluate_rubric(content, filename=filename)
    cl, o = res["tokens"]
    lines = []
    lines.append("=" * 80)
    lines.append(f"7-PILLAR RUBRIC EVALUATION SCORECARD: {filename or 'Prompt'}")
    lines.append("=" * 80)
    lines.append(f"Score: {res['score']} / {res['max_score']} | cl100k: {cl:,} | o200k: {o:,} | Verdict: {'PASS' if res['passed'] else 'FAIL'}")
    lines.append("-" * 80)

    pillar_titles = {
        "1_goal_and_done_criteria": "1. Goal & Done-Criteria",
        "2_information_hierarchy_and_caching": "2. Information Hierarchy & Caching",
        "3_positive_framing_and_anti_cruft": "3. Positive Framing & Anti-Cruft",
        "4_guardrails_and_invariants": "4. Guardrails & Invariants",
        "5_grounding_and_verification": "5. Grounding & Verification Loop",
        "6_target_harness_alignment": "6. Target Harness & Tool Alignment",
        "7_token_efficiency_and_hygiene": "7. Token Efficiency & Context Hygiene",
    }

    for key, title in pillar_titles.items():
        p = res["pillars"][key]
        status = "[✓] PASS" if p["passed"] else "[✗] FAIL"
        lines.append(f"{status:<10} | {title:<36} | {p['detail']}")

    if res["cruft_items"]:
        lines.append("-" * 80)
        lines.append(f"Cruft Findings ({len(res['cruft_items'])}):")
        for idx, item in enumerate(res["cruft_items"], 1):
            lines.append(f"  [{idx}] Line {item['line']}: {item['pattern']} -> {item['action']}")

    lines.append("=" * 80)
    return "\n".join(lines)


# ==============================================================================
# 2. OpenAI Evals cot_classify & Reverse-Line Parsing
# ==============================================================================

def build_cot_classify_prompt(task_objective: str, candidate_prompt: str, choices: list[str], criteria: str = "") -> str:
    """
    Constructs a cot_classify evaluation prompt following the OpenAI Evals standard
    (documented in references/best-practices.md Section 13).
    """
    choices_str = ", ".join(f'"{c}"' for c in choices)
    criteria_block = f"\nCriteria:\n{criteria}\n" if criteria else ""
    return f"""You are an automated prompt quality evaluator.
Task Objective:
{task_objective}
{criteria_block}
Candidate Prompt Content:
```markdown
{candidate_prompt}
```

First, write out in a step by step manner your reasoning to be sure that your conclusion is correct.
Avoid simply stating the correct answer at the outset.
Then print only a single choice from [{choices_str}] (without quotes or punctuation) on its own line corresponding to the correct answer.
At the end, repeat just the answer by itself on a new line.

Reasoning:
"""


def parse_reverse_line_choice(completion: str, choices: list[str]) -> str | None:
    """
    Reverse-Line Parsing (Section 13 of references/best-practices.md):
    Splits completion lines and parses in reverse (`lines[::-1]`) to match
    against valid choice strings, guaranteeing robust verdict extraction
    despite verbose chain-of-thought deliberations.
    """
    if not completion or not completion.strip():
        return None

    norm_choices = {c.strip().lower(): c for c in choices}
    lines = completion.strip().splitlines()

    for line in reversed(lines):
        clean = line.strip().strip("*_`'\"#[]()").strip()
        clean = re.sub(r"^(choice|verdict|answer)\s*:\s*", "", clean, flags=re.IGNORECASE).strip()
        clean_lower = clean.lower()

        if clean_lower in norm_choices:
            return norm_choices[clean_lower]

    return None


# ==============================================================================
# 3. Token Tax & Fracture Zone Bounds
# ==============================================================================

def calculate_token_tax(tokens: int, turns: int = 20) -> dict:
    """
    Calculates cumulative session input token consumption and checks
    against the 200k attention context 60% fracture threshold.
    """
    cumulative = tokens * turns
    uncached_cost = (cumulative / 1_000_000) * 3.0
    cached_cost = (cumulative / 1_000_000) * 0.30
    utilization_200k = (cumulative / 200_000) * 100
    fracture_zone_warning = utilization_200k >= 60.0

    return {
        "base_tokens": tokens,
        "turns": turns,
        "cumulative_tax": cumulative,
        "uncached_cost_usd": uncached_cost,
        "cached_cost_usd": cached_cost,
        "utilization_200k_pct": utilization_200k,
        "fracture_zone_warning": fracture_zone_warning,
    }


# ==============================================================================
# 4. Regression Test Suite & Fixtures
# ==============================================================================

FIXTURE_GOLD_BRIEF = """---
created: 2026-09-10
mode: coding-agent-brief
target_model: agy (Antigravity 2.0 / Gemini 3.8)
intent: Fix connection pool race condition in backend worker
---

<role>
You are an autonomous senior software engineer working in the backend service repository.
</role>

<context>
Target codebase: Connection manager and async pool worker under src/pool/.
Task context: Fix connection pool race condition during worker teardown.
Keep static invariants here at the top to preserve prompt cache prefixes.
</context>

<task>
Fix the connection pool race condition during concurrent checkout and worker teardown.

Observable Done Criteria:
1. Prevent leaked sockets when workers terminate while checkout requests are queued.
2. Synchronize connection pool state using async locks with bounded timeout.
3. Add concurrency regression test reproducing the race condition and confirming resolution.
</task>

<constraints>
- Scope ceiling: Confine modifications to src/pool/manager.py and tests/test_pool_concurrency.py. Do not refactor unrelated networking code.
- Anti-slurp: Inspect files with targeted line bounds (`rg -n -C 1`, `git diff --stat`). Never dump whole files >150 lines.
- Surgical diffs: Apply minimal targeted edits or unified diffs; never echo back unchanged code blocks.
- Tool boundaries: Use dedicated file-reading/editing tools over raw shell redirection (`cat > file`) to allow harness staleness checks.
- Harness Directives Mandate: Treat this brief as an imperative Directive; proceed directly to exploration, plan artifact generation, and implementation.
- Post-edit silence: After code modifications, run tests silently without echoing verbose test suite logs.
</constraints>

<verification>
Run verification commands and confirm clean exit code 0:
1. `pytest tests/test_pool_concurrency.py -k test_checkout_race`
2. `ruff check src/pool/manager.py`
</verification>

<output>
Provide a concise summary of root cause, surgical diff of modifications, and verification test outcomes. Do not echo full unmodified files.
</output>
"""

FIXTURE_CRUFT_BRIEF = """---
created: 2026-09-10 14:32
mode: coding-agent-brief
---

You are a programmer.
CRITICAL: You MUST fix the connection bug immediately and NEVER make mistakes!!
Be thorough, do not be lazy.
Think step by step before answering.
Output ONLY valid JSON.
Please run with gemini-1.5-pro.

Dump the entire file content here into the chat response.
"""


def run_eval_suite() -> bool:
    """Executes the full automated regression suite."""
    print("================================================================================")
    print("PROMPTSMITH AUTOMATED 7-PILLAR RUBRIC & EVAL REGRESSION SUITE")
    print("================================================================================")
    tests_run = 0
    failures = []

    # --- Test 1: Gold-standard prompt passes 7/7 pillars ---
    tests_run += 1
    gold_res = evaluate_rubric(FIXTURE_GOLD_BRIEF, filename="fixture_gold_brief.md")
    if gold_res["score"] == 7 and gold_res["cruft_count"] == 0 and gold_res["hygiene"]["anti_slurp"] and gold_res["hygiene"]["diff_contract"]:
        print("[✓] PASS: Fixture Gold Brief scores 7/7 on rubric with 0 cruft")
    else:
        failures.append(f"Fixture Gold Brief failed: score={gold_res['score']}/7, cruft={gold_res['cruft_count']}")
        print(f"[✗] FAIL: Fixture Gold Brief: {failures[-1]}")

    # --- Test 2: Cruft fixture fails and flags all anti-patterns ---
    tests_run += 1
    cruft_res = evaluate_rubric(FIXTURE_CRUFT_BRIEF, filename="fixture_cruft_brief.md")
    if cruft_res["cruft_count"] >= 5 and not cruft_res["pillars"]["3_positive_framing_and_anti_cruft"]["passed"] and not cruft_res["pillars"]["7_token_efficiency_and_hygiene"]["passed"] and cruft_res["hygiene"]["cache_warning"]:
        print(f"[✓] PASS: Fixture Cruft Brief correctly flagged {cruft_res['cruft_count']} cruft items & failed hygiene")
    else:
        failures.append(f"Fixture Cruft Brief did not trigger expected failures: cruft_count={cruft_res['cruft_count']}")
        print(f"[✗] FAIL: Fixture Cruft Brief: {failures[-1]}")

    # --- Test 3: OpenAI Evals Reverse-Line Parsing ---
    tests_run += 1
    choices = ["PASS", "FAIL"]
    
    noisy_completion_pass = """
    First, write out in a step by step manner your reasoning.
    The prompt contains extensive context and structured delimiters.
    Initially I considered whether it might FAIL due to length.
    However, the length is load-bearing and includes anti-slurp bounds and diff contracts.
    Therefore, the rubric requirements are completely satisfied.
    PASS
    PASS
    """
    parsed_pass = parse_reverse_line_choice(noisy_completion_pass, choices)

    noisy_completion_fail = """
    Reasoning:
    Examining the prompt...
    Line 3 contains shouting caps.
    Line 7 uses obsolete think step by step incantation.
    Conclusion: The candidate violates anti-cruft rules.
    Verdict: FAIL
    FAIL
    """
    parsed_fail = parse_reverse_line_choice(noisy_completion_fail, choices)

    markdown_bold_pass = """
    Evaluation completed.
    All criteria met.
    **PASS**
    """
    parsed_md = parse_reverse_line_choice(markdown_bold_pass, choices)

    if parsed_pass == "PASS" and parsed_fail == "FAIL" and parsed_md == "PASS":
        print("[✓] PASS: OpenAI Evals cot_classify reverse-line parsing robust to noisy reasoning traces")
    else:
        failures.append(f"Reverse-line parsing failed: pass={parsed_pass}, fail={parsed_fail}, md={parsed_md}")
        print(f"[✗] FAIL: Reverse-line parsing: {failures[-1]}")

    # --- Test 4: Token Tax & Fracture Zone Bounds ---
    tests_run += 1
    tax_healthy = calculate_token_tax(tokens=2000, turns=20)
    tax_fracture = calculate_token_tax(tokens=7000, turns=20)

    if (
        tax_healthy["cumulative_tax"] == 40000
        and not tax_healthy["fracture_zone_warning"]
        and tax_fracture["cumulative_tax"] == 140000
        and tax_fracture["fracture_zone_warning"]
    ):
        print("[✓] PASS: Token tax calculations and 60% fracture zone boundary assertions verified")
    else:
        failures.append(f"Token tax assertions failed: healthy={tax_healthy}, fracture={tax_fracture}")
        print(f"[✗] FAIL: Token tax assertions: {failures[-1]}")

    # --- Test 5: Self-Verification on Promptsmith Reference Files ---
    tests_run += 1
    repo_root = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
    ref_files = [
        "SKILL.md",
        "references/best-practices.md",
        "references/coding-agent-brief.md",
        "references/harness-notes.md",
        "references/repo-rules.md",
        "references/general-llm-prompt.md",
    ]
    ref_cruft_total = 0
    for rf in ref_files:
        full_p = os.path.join(repo_root, rf)
        if os.path.exists(full_p):
            with open(full_p, "r", encoding="utf-8") as f:
                c = f.read()
            findings = find_cruft(c, filename=rf)
            ref_cruft_total += len(findings)

    if ref_cruft_total == 0:
        print("[✓] PASS: Self-Verification: All Promptsmith repo reference files audit with 0 cruft findings")
    else:
        failures.append(f"Promptsmith reference files contain {ref_cruft_total} false-positive cruft findings")
        print(f"[✗] FAIL: Self-Verification: {failures[-1]}")

    # --- Test 6: GLM-5.3 Prompt Generation & Rubric Compliance ---
    tests_run += 1
    try:
        from token_audit import generate_prompt
        glm_brief = generate_prompt(mode="brief", intent="Implement billing webhook for subscription updates", target_model="GLM-5.3")
        glm_res = evaluate_rubric(glm_brief, filename="generated_glm_brief.md")
        if (
            glm_res["score"] == 7
            and glm_res["cruft_count"] == 0
            and "GLM-5.3" in glm_brief
            and glm_res["hygiene"]["anti_slurp"]
            and glm_res["hygiene"]["diff_contract"]
        ):
            print("[✓] PASS: GLM-5.3 prompt generation and 7-pillar rubric compliance verified")
        else:
            failures.append(f"GLM-5.3 prompt generation rubric check failed: score={glm_res['score']}/7, cruft={glm_res['cruft_count']}")
            print(f"[✗] FAIL: GLM-5.3 Prompt Generation: {failures[-1]}")
    except Exception as e:
        failures.append(f"GLM-5.3 prompt generation test error: {e}")
        print(f"[✗] FAIL: GLM-5.3 Prompt Generation: {e}")

    # --- Test 7: Fenced Code Block Directives vs Benign Code/Config Syntax ---
    tests_run += 1
    doc_fenced_directive = """
```bash
# CRITICAL: You MUST ALWAYS run this!
```
"""
    doc_benign_code = """
```python
pattern = re.compile(r"CRITICAL|MUST")
log_level = "CRITICAL"
```
"""
    doc_benign_config = """
```yaml
logging:
  level: CRITICAL
```
"""
    f_directive = find_cruft(doc_fenced_directive, filename="fenced_directive.md")
    f_code = find_cruft(doc_benign_code, filename="benign_code.py")
    f_config = find_cruft(doc_benign_config, filename="benign_config.yaml")

    if len(f_directive) >= 1 and len(f_code) == 0 and len(f_config) == 0:
        print("[✓] PASS: Fenced directives audited while benign code/config examples remain clean")
    else:
        failures.append(f"Fenced cruft discrimination failed: directive_findings={len(f_directive)}, code_findings={len(f_code)}, config_findings={len(f_config)}")
        print(f"[✗] FAIL: Fenced Cruft Discrimination: {failures[-1]}")

    # --- Test 8: Environment Capabilities Discovery & Prompt Injection ---
    tests_run += 1
    try:
        from env_discovery import scan_environment, filter_by_query, format_prompt_context
        from token_audit import generate_prompt

        env_data = scan_environment()
        assert env_data["counts"]["total"] > 0, "No environment capabilities discovered"
        assert len(env_data["skills"]) > 0, "No skills discovered"

        filtered = filter_by_query(env_data, "devtools")
        xml_context = format_prompt_context(filtered)
        assert "<available_environment_capabilities>" in xml_context
        assert "</available_environment_capabilities>" in xml_context

        generated_brief = generate_prompt(
            mode="brief",
            intent="Debug and resolve web accessibility violations",
            target_model="agy (Antigravity 2.0 / Gemini 3.8)",
            env_context=xml_context,
        )
        gen_rubric = evaluate_rubric(generated_brief, filename="generated_env_brief.md")
        if gen_rubric["score"] == 7 and gen_rubric["cruft_count"] == 0:
            print("[✓] PASS: Environment discovery and prompt capability injection verified (7/7 on rubric)")
        else:
            failures.append(f"Environment capability injection prompt failed rubric: score={gen_rubric['score']}/7, cruft={gen_rubric['cruft_count']}")
            print(f"[✗] FAIL: Environment Discovery & Prompt Injection: {failures[-1]}")
    except Exception as e:
        failures.append(f"Environment discovery test error: {e}")
        print(f"[✗] FAIL: Environment Discovery & Prompt Injection: {e}")

    print("--------------------------------------------------------------------------------")
    if not failures:
        print(f"ALL {tests_run} REGRESSION SUITE CHECKS PASSED WITH ZERO ERRORS.")
        print("================================================================================")
        return True
    else:
        print(f"FAILED {len(failures)} of {tests_run} regression checks.")
        print("================================================================================")
        return False


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ("--test", "-t"):
        # Evaluate provided files
        all_passed = True
        for arg in sys.argv[1:]:
            if arg in ("-", "--stdin"):
                content = sys.stdin.read()
                print(format_rubric_report(content, filename="<stdin>"))
                res = evaluate_rubric(content, filename="<stdin>")
                if not res["passed"]:
                    all_passed = False
            elif os.path.exists(arg):
                with open(arg, "r", encoding="utf-8") as f:
                    content = f.read()
                print(format_rubric_report(content, filename=arg))
                res = evaluate_rubric(content, filename=arg)
                if not res["passed"]:
                    all_passed = False
            else:
                print(f"File not found: {arg}")
                all_passed = False
        sys.exit(0 if all_passed else 1)

    success = run_eval_suite()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
