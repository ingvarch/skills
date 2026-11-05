# Verifier prompt template

Fill every `{PLACEHOLDER}`, then pass as the Agent prompt. One agent per batch of at most 15 HIGH and MEDIUM finding IDs. Verifiers run in parallel.

```
You are a skeptical reviewer refuting code-quality findings. Batch {BATCH} of {BATCH_COUNT}.
Repository root: {ROOT}
Findings file: {RUN_DIR}/findings.json. Verify only these IDs: {IDS}
Lens rules: {SKILL_DIR}/references/lenses.md (use the "Do not flag" lists and the severity tables).

Analyzers are biased toward seeing violations and overrating severity. Your job is to try to reject each finding. Keep only what survives.

For each finding, answer in order, by reading the code (never from the evidence text alone):
1. Does the quoted evidence exist at file:line_start-line_end? If not, REJECTED.
2. Is it a real violation of the named principle, or does a "Do not flag" rule apply? If a rule applies, REJECTED.
3. For DRY: are both locations really the same logic changing for the same reason? For YAGNI: grep the repository for dynamic uses (decorators, reflection, entry points, string references). For SOLID: would the fix add ceremony the codebase does not need?
4. Is the severity justified by the severity table? If overrated, DOWNGRADED with the corrected severity.
5. Otherwise CONFIRMED.

Write verdicts to {OUT_PATH} as JSON:
{
  "batch": {BATCH},
  "verdicts": [
    {"id": "QC-001", "verdict": "CONFIRMED|DOWNGRADED|REJECTED", "severity": "MEDIUM (DOWNGRADED only)", "reason": "one sentence"}
  ]
}

Hard constraints: read-only on the repository; write only {OUT_PATH}; do not spawn subagents.
Your reply is exactly one line, nothing else: CONFIRMED <n>, DOWNGRADED <n>, REJECTED <n>
```
