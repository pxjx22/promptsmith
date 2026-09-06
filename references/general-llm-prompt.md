# General LLM prompt

A prompt for a single model call (or a reusable system prompt applied to
many inputs): analysis, extraction, classification, summarising,
transformation, conversation, or structured data output.

## Question pool

Ask only the items the request leaves genuinely open. Max 4, one round,
each with a recommended default.

1. **Task & success criteria** — what should the model produce, and what
   makes an output good vs. bad?
2. **Input** — what data or text does the prompt receive? How large, what
   format, how variable?
3. **Output format** — prose, JSON schema, markdown list, or specific tag structure?
   Rough length? Any field it must always include?
4. **Audience & tone** — who reads the output, how formal, any voice?
5. **Role / persona** — what expertise should the model adopt?
6. **Examples** — can the user supply 1–2 real input->output pairs? If
   not, should the prompt generate illustrative ones?
7. **Boundaries** — what to avoid, known edge cases, fallback rules when data is missing?
8. **Reuse** — one-off user prompt, or an automated pipeline/system prompt run
   against thousands of inputs?

## Base Template

```markdown
<role>
You are <persona with relevant domain expertise>.
</role>

<context>
<Why this task exists, who consumes the output, and domain definitions.
Place long reference documents or background data here, near the top.>
</context>

<document>            <!-- Include only if there is a long input text -->
{{INPUT}}
</document>

<instructions>
<The task as direct instructions. Use a numbered list if order/completeness matters.
State what to do using positive framing, not what to avoid.>
1. First, quote the exact passages relevant to the query.
2. Analyze the extracted evidence against <criteria>.
3. Synthesize the final conclusion in <output_format>.
</instructions>

<examples>
<example>
Input: <short representative input>
Output: <the ideal output for it>
</example>
<!-- 3–5 diverse examples; cover edge cases; mark generated ones:
     example — replace with a real case -->
</examples>

<output_format>
<Exact shape: "Return a JSON object with schema...", or "Write 2-3 paragraphs of prose".
Specify length, key constraints, and state: "Start directly with the output; do not include conversational preambles.">
</output_format>
```

---

## Output Patterns

### Pattern A: Strict JSON / Schema Output
Use for API pipelines, function calling, or tool chaining where parse errors break code.

```markdown
<instructions>
Extract the specified entities from the text below and return a valid JSON object.
Do not include markdown code fences, conversational greetings, or trailing notes.
Start immediately with `{` and end with `}`.
</instructions>

<input>
{{INPUT}}
</input>

<output_schema>
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "summary": {"type": "string"},
    "status": {"type": "string", "enum": ["healthy", "degraded", "failing"]},
    "metrics": {
      "type": "object",
      "properties": {
        "error_rate": {"type": "number"},
        "latency_p99_ms": {"type": "integer"}
      },
      "required": ["error_rate", "latency_p99_ms"]
    }
  },
  "required": ["summary", "status", "metrics"]
}
</output_schema>
```

### Pattern B: Few-Shot Categorization & Triage (Class-Balanced)
Use when classifying messy text into controlled buckets.
*Rule from Google Whitepaper & Zhao et al.:* Balance classes across examples and randomize their order to prevent recency and majority-label bias.

```markdown
<role>
You are an operations triage specialist.
</role>

<instructions>
Classify the following incoming report into exactly one category: [SECURITY, HARDWARE, NETWORK, APPLICATION].
Provide a 1-sentence rationale citing specific phrases from the input.
</instructions>

<examples>
<example>
Input: "Ethernet link flapping on eth0 during high rx load"
Output: CATEGORY: NETWORK
Rationale: Mentions Ethernet link state transitions and rx packet load.
</example>
<example>
Input: "Failed SSH login attempts from untrusted IP pool with invalid keys"
Output: CATEGORY: SECURITY
Rationale: Involves unauthorized authentication attempts and untrusted IP origins.
</example>
<example>
Input: "Memory allocation fault in payment-gateway worker pool"
Output: CATEGORY: APPLICATION
Rationale: Traces an OOM condition inside the user-space application worker runtime.
</example>
<example>
Input: "NVMe drive /dev/nvme0n1 reporting SMART media errors and high wear"
Output: CATEGORY: HARDWARE
Rationale: Relates to physical storage block wear and controller hardware telemetry.
</example>
</examples>

<input>
{{INPUT}}
</input>
```

### Pattern C: Step-Back Prompting for Complex Reasoning
Use for complex analytical, mathematical, architectural, or domain-specific reasoning.
*Rule from Google DeepMind (Zheng et al.):* Ask the model to first evoke the foundational abstraction before solving the specific instance.

```markdown
<role>
You are a principal systems architect.
</role>

<instructions>
Answer the query using a two-step reasoning approach:
Step 1 (Step-Back): State the foundational principles, architectural constraints, and failure modes governing this class of problem in <first_principles> tags.
Step 2 (Analysis): Apply those principles directly to the specific scenario in {{INPUT}} to produce your final recommendation in <recommendation> tags.
</instructions>

<input>
{{INPUT}}
</input>
```

### Pattern D: Prompt Compressor & Token Minifier
Use for auditing and compressing bloated prompts, system instructions, or briefs (targeting 40%–60% token reduction).

```markdown
<role>
You are an expert prompt engineer and LLM token optimization specialist.
</role>

<context>
The user provides an existing prompt, system rule file, or coding brief that consumes excessive context tokens.
Your objective is to minify the prompt while retaining 100% of its operational constraints, safety boundaries, and task objectives.
</context>

<instructions>
Minify the target prompt according to these strict rules:
1. Dead weight pruning: Remove conversational greetings, generic filler ("You are an AI that strives to be helpful"), and redundant restatements of model defaults.
2. Structural flattening: Convert dense narrative prose into high-density bullet tables or compact XML.
3. Pointer substitution: In coding briefs, point at files/configs (`@Cargo.toml`, `@src/`) instead of summarizing them.
4. Positive constraint consolidation: Consolidate scattered prohibitions into unified, bounded rules.
5. Anti-slurp & Diff enforcement: Inject bounded tool directives and diff-first output contracts.
6. Cache stabilization: Ensure static instructions are at the top and dynamic variables are at the bottom.
</instructions>

<input>
{{BLOATED_PROMPT}}
</input>

<output_format>
Return strictly:
1. The minified prompt in a fenced code block.
2. A single-line token delta: `~<before> → ~<after> tokens (-<pct>%), estimated 20-turn context savings: -<tax> tokens`.
Do not include conversational preamble or commentary.
</output_format>
```

---

## Sampling Parameters Recommendation

Include recommended sampling parameters in the prompt metadata:
- **Code, Math, Logic, Extraction, JSON Schema, Compression:** `temperature: 0.0` or `0.2` (greedy decoding for consistency and structural guarantees).
- **Writing, Synthesis, Ideation:** `temperature: 0.7 - 0.9`, `top_p: 0.9` (lexical diversity and creative variation).

---

## Prompt Improvement & Critique Rubric (7 Pillars)

When performing an *improve* or *compress* run on an existing prompt, evaluate it across these 7 pillars:

1. **Clarity & Success Metric:** Is the goal explicit? Is "done" or "high quality" defined rather than assumed?
2. **Information Ordering & Caching:** Are reference documents/data placed *before* instructions? Is static context preserved at the root?
3. **Framing & Guidance:** Are negative prohibitions replaced with affirmative instructions? Is the *why* explained for non-obvious rules?
4. **Structural Delimiters:** Are sections cleanly separated with XML-style tags (`<instructions>`, `<context>`, `<output_format>`)?
5. **Examples & Class Balance:** Are 3–5 diverse examples included with balanced classes and varied label sequences?
6. **Output Rigor & Preamble Control:** Is the output shape airtight? Are conversational preambles ("Sure, here is...") eliminated?
7. **Token Efficiency & Context Hygiene:** Are anti-slurp bounds enforced? Are dynamic timestamps removed from cached prefixes? Are outputs diff-first? Is the prompt density maximized (no narrative fluff)?
