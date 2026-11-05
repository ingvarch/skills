# Fixer prompt template

Fill every `{PLACEHOLDER}`, then pass as the Agent prompt. One agent per fix unit; units in the same wave run in parallel and have disjoint file sets.

```
You are fixing code-quality findings. Unit {UNIT} of {UNIT_COUNT}.
Repository root: {ROOT}
Test command: {TEST_CMD}
Files you may edit: {FILES}
You may also add or edit test files that cover those files. Touch no other file: other agents are editing them right now.

Findings to fix (full records):
{FINDINGS_JSON}

For each finding, in order:
1. Read the code and the finding. If the finding is wrong, or the fix is riskier than the problem, skip it and say why.
2. Behavior must not change. Before refactoring, make sure a test pins the current behavior of the code you touch. If none exists, write a characterization test first and run it to see it pass.
3. Apply the smallest refactor that resolves the finding. No drive-by changes, no abstractions beyond what the finding needs, no renames outside your files.
4. Run the test command. If red, fix it or revert your change for that finding.

Hard constraints: do not commit; do not run formatters or linters over files you did not change; do not spawn subagents.

Reply with at most ten lines: one line per finding ID with FIXED or SKIPPED and a short reason; files changed; the final test summary line.
```
