# Aggregator prompt template

Fill every `{PLACEHOLDER}`, then pass as the Agent prompt. One agent, after verdicts are applied.

```
You are writing the report for a code-quality audit.
Repository root: {ROOT}
Run directory: {RUN_DIR}

Read, in this order:
1. {RUN_DIR}/inventory.json: scope (empty list means the whole repository), file count, LOC, chunks, agent count, oversized flag.
2. {RUN_DIR}/findings.json: summary, findings with their verified status and overlaps_with, rejected list.
3. The "notes" field of every {RUN_DIR}/raw/*.json.

Write {RUN_DIR}/report.md following {SKILL_DIR}/references/report-template.md exactly: same sections, same order, same per-finding layout. Use the IDs, severities, and counts from findings.json without changing them. Do not re-audit the code; you may open a file only to pick a language tag for an evidence block.

Hard constraints: write only {RUN_DIR}/report.md; do not modify any other file; do not spawn subagents.
Reply in at most five lines: report path, total findings, the headline theme, anything the user must know about coverage.
```
