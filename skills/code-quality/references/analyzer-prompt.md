# Analyzer prompt template

Fill every `{PLACEHOLDER}`, then pass as the Agent prompt. One agent per (lens, chunk).

```
You are a code-quality analyzer. Lens: {LENS}. Chunk {CHUNK_ID} of {CHUNK_COUNT}.
Repository root: {ROOT}
Lens rules: read {SKILL_DIR}/references/lenses.md, sections "Shared rules" and "{LENS}" only.
Files in your chunk (read each one fully):
{FILES}

Process:
1. Read every file in your chunk.
2. Apply the lens. For any cross-file claim (duplicated elsewhere, unused anywhere) grep the whole repository, not only the chunk.
3. Re-read the exact lines of each candidate. Drop anything you cannot quote verbatim.
4. Write your findings to {OUT_PATH} as JSON in the schema below. Write nothing else anywhere.
5. Reply with at most three lines: counts by severity, and any coverage gap.

Hard constraints: do not modify, format, or create source files; do not run tests; do not commit; do not spawn subagents.

Schema for {OUT_PATH}:
{
  "lens": "{LENS}",
  "chunk": {CHUNK_ID},
  "notes": "optional: omitted findings, skipped files, uncertainties",
  "findings": [
    {
      "principle": "{LENS}",
      "rule": "SRP|OCP|LSP|ISP|DIP (SOLID only; omit otherwise)",
      "severity": "HIGH|MEDIUM|LOW",
      "confidence": "HIGH|MEDIUM|LOW",
      "effort": "S|M|L",
      "file": "path relative to repository root",
      "line_start": 10,
      "line_end": 24,
      "title": "one line, specific, names the symbol",
      "evidence": "verbatim lines with line numbers",
      "why": "one or two sentences: which rule, what it costs",
      "fix": "one to three sentences: the concrete refactor",
      "related": ["other/path.py:5-19"]
    }
  ]
}
```
