# Report template

The aggregator writes `report.md` in the run directory with exactly these sections. Fill from `findings.json` (ids, counts) and the analyzers' `notes` in `raw/*.json`.

Findings whose `overlaps_with` lists other IDs describe one root cause seen through several lenses. Present them once under the strongest severity: the heading carries every ID and principle (`QC-010, QC-011 [SOLID/ISP, YAGNI]`), with one evidence block and one combined fix. The LOW table still lists each ID on its own row.

```markdown
# Code Quality Report

Run: {RUN_ID}
Scope: {SCOPE}
Files: {FILE_COUNT} | LOC: {TOTAL_LOC} | Chunks: {CHUNK_COUNT} | Analyzers: {AGENT_COUNT}

## Summary

| | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|
| DRY | | | | |
| KISS | | | | |
| YAGNI | | | | |
| SOLID | | | | |
| Total | | | | |

Two to four sentences: overall state, the two or three themes that explain most findings, the one change with the highest payoff.

## Findings

### HIGH

#### QC-001 [DRY] {title}
- Where: `{file}:{line_start}-{line_end}`; related: `{related}`
- Why: {why}
- Fix: {fix} (effort {effort}, confidence {confidence})

```{lang}
{evidence}
```

### MEDIUM

Same layout as HIGH.

### LOW

| ID | Principle | Where | Title | Effort |
|---|---|---|---|---|

## Recommended fix order

Numbered list. Quick wins first (HIGH with effort S), then by severity. Group findings that touch the same files into one step and say so.

## Coverage notes

- Chunks and budget; whether the scope was oversized and analysis was coarser than usual.
- Analyzer notes: omitted findings, skipped files, uncertainties.
- Merge stats: dropped invalid, merged duplicates, unreadable files.

## Done well

Two to five bullets naming patterns worth keeping. Skip the section if nothing stands out.
```
