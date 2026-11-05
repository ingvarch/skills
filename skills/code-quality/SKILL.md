---
name: code-quality
description: Audit a repository, some paths or the changed files for DRY, KISS, YAGNI and SOLID problems with parallel analyzer agents and a refuting verifier, write a report of file:line findings, and fix the findings the user picks on a branch, test first. Use when the user asks for a code-quality audit or report, or to fix findings of an earlier code-quality run.
argument-hint: "[path ...] | --changed | fix [HIGH|MEDIUM|LOW|QC-001,QC-002]"
disable-model-invocation: true
---

# code-quality

Fan out one analyzer agent per (principle, chunk), let a skeptical verifier refute what they found,
and only then write a report. Agents write their findings to files and reply in a few lines, so the
main context stays small. You run the scripts and dispatch the agents. Until the gate, the only
writes are the run directory and a git exclude entry for it; no source file changes before the user
says which findings to fix.

Names used below:

- `<skill>`: this skill's folder, the base directory shown when it loads. The prompts in
  `references/` call its absolute path `{SKILL_DIR}`.
- `ROOT`: `git rev-parse --show-toplevel`, absolute.
- `RUN_ID`: `date +%Y%m%d-%H%M%S`.
- `RUN_DIR`: `ROOT/.code-quality/RUN_ID`, absolute. Always pass absolute paths to agents.

Scripts run with `python3 -I`; each has `--help`.

## Arguments

Arguments given: `$ARGUMENTS`. They select the mode:

| Arguments | Mode |
|---|---|
| empty | Audit the whole repository |
| one or more paths | Audit only those paths |
| `--changed` | Audit the files changed against the default branch, plus the working tree |
| `fix` | Fix the HIGH findings of the newest run |
| `fix MEDIUM` or `fix LOW` | Fix the findings at that severity and above |
| `fix QC-003,QC-007` | Fix exactly those IDs |

An audit runs steps 1 to 4, then the gate (step 5), then step 6 when the user opts in. Fix mode
starts at the gate with the newest `ROOT/.code-quality/*/findings.json`.

## 1. Scope

1. Resolve `ROOT`. Not a git repository: stop and say so.
2. For `--changed`, the scope is `git diff --name-only $(git merge-base HEAD <default-branch>)` plus
   the `git status --porcelain` paths. Default branch: `origin/HEAD`, else `main`, else `master`.
3. Create the run directory and the inventory:

   ```bash
   mkdir -p RUN_DIR/raw RUN_DIR/verdicts
   python3 -I <skill>/scripts/inventory.py --root ROOT --scope <paths> > RUN_DIR/inventory.json
   ```

   Leave out `--scope` for the whole repository.
4. When `git -C ROOT check-ignore -q .code-quality` fails, append `/.code-quality/` to the file that
   `git -C ROOT rev-parse --path-format=absolute --git-path info/exclude` prints. That file is local
   and not tracked, so the working tree stays clean. Tell the user in one line.
5. Tell the user in one line: files, LOC, chunks, analyzer count. When `oversized` is true or
   `agent_count` is over 8, use AskUserQuestion before dispatching: proceed, or narrow the scope
   with paths.
6. Zero source files: stop and say so.

The inventory leaves out vendored, generated and minified code, and packs directories into chunks of
at most 5000 non-blank LOC, at most 4 chunks. Change `--budget` and `--max-chunks` only when the
user asks.

Done when `RUN_DIR/inventory.json` exists and the user has seen the counts.

## 2. Analyze

Dispatch every analyzer in a single message, so they run in parallel. One Agent per (lens, chunk),
`subagent_type: general-purpose`, with a prompt built from `<skill>/references/analyzer-prompt.md`:

- `LENS`: DRY, KISS, YAGNI or SOLID
- `FILES`: the chunk's file list from the inventory
- `OUT_PATH`: `RUN_DIR/raw/<LENS>-<chunk>.json`
- `SKILL_DIR`, `ROOT`, `CHUNK_ID`, `CHUNK_COUNT`

Analyzers only read, and reply in at most three lines. Do not read their JSON files in the main
thread.

Done when every analyzer has replied and `RUN_DIR/raw/` holds one file per analyzer.

## 3. Merge and verify

1. Merge, validate, dedupe and assign IDs. The command prints the severity by principle table:

   ```bash
   python3 -I <skill>/scripts/merge_findings.py --run-dir RUN_DIR
   ```

2. List the findings to verify and split the IDs into batches of at most 15:

   ```bash
   python3 -I <skill>/scripts/merge_findings.py --run-dir RUN_DIR --brief HIGH,MEDIUM
   ```

   Dispatch one verifier per batch in a single message, with the prompt from
   `<skill>/references/verifier-prompt.md`: `BATCH` and `BATCH_COUNT` = the batch number and the
   number of batches, `IDS` = the batch's IDs, `OUT_PATH` = `RUN_DIR/verdicts/<BATCH>.json`, and
   `ROOT`, `RUN_DIR`, `SKILL_DIR`. Verifiers read `findings.json` themselves; do not paste finding
   records into the prompt.
3. Apply the verdicts. Rejected findings move to `rejected`, downgraded ones change severity, and
   findings no verifier saw are marked UNVERIFIED:

   ```bash
   python3 -I <skill>/scripts/merge_findings.py --run-dir RUN_DIR --apply-verdicts
   ```

With zero HIGH and MEDIUM findings after the merge, skip the verifiers and still run
`--apply-verdicts`, so every finding carries a `verified` field.

Done when every finding in `RUN_DIR/findings.json` has a `verified` field.

## 4. Report

Dispatch one aggregator Agent (`general-purpose`) with the prompt from
`<skill>/references/aggregator-prompt.md`, filled with `ROOT`, `RUN_DIR` and `SKILL_DIR`. It writes
`RUN_DIR/report.md` and replies in at most five lines.

Then show the user:

- the severity by principle table printed by `--apply-verdicts`;
- the output of `--brief HIGH`, and the MEDIUM count;
- the counts of rejected and downgraded findings, so the user sees the verifier worked;
- the report path.

Done when `RUN_DIR/report.md` exists and the user has its path.

## 5. Gate

Use AskUserQuestion with one question, "Fix findings now?", and the options HIGH only (recommended),
HIGH and MEDIUM, everything, not now. Put the name of the branch the fixes go to in the question
text. "Not now" ends the skill with the report path and the `fix` argument form for later.

When the user gave `fix ...` arguments, skip the question about scope but still confirm once: the
run ID, the number of findings selected and the branch.

Done when the user has picked the findings to fix, or ended the skill.

## 6. Fix

Preconditions, in order; stop with a message when one fails:

1. `git status --porcelain` is empty. Do not stash or commit for the user.
2. The test command is known. Detect it from the project (pytest, `npm test`, `go test ./...`,
   `cargo test`, `make test`). Unknown: ask with AskUserQuestion. No tests at all: the user must
   confirm going on without a safety net.
3. The test command passes on the current tree.

Then:

1. `git switch -c refactor/code-quality-RUN_ID`. When an earlier fix of this run made the branch,
   `git switch refactor/code-quality-RUN_ID`.
2. Plan units with disjoint file sets, in parallel waves:

   ```bash
   python3 -I <skill>/scripts/plan_fixes.py --findings RUN_DIR/findings.json --min-severity <severity>
   ```

   `<severity>` is the one the user picked; use `--ids` for an explicit ID list. On a later fix of
   the same run, the IDs in `git log --format=%s <default-branch>..HEAD` are fixed already: pass
   `--ids` with the rest. Show the user the units (IDs and files) before the first wave. Findings
   that share files merge into one unit, so a broad severity can produce one large unit. When
   `oversized_units` is not empty, say so and use AskUserQuestion: fix that unit as one large
   refactor, or narrow to HIGH first and run the rest afterwards.
3. For each wave, dispatch one fixer Agent per unit in a single message, with the prompt from
   `<skill>/references/fixer-prompt.md`: `UNIT` and `UNIT_COUNT` = the unit number and the number
   of units, `FINDINGS_JSON` = the unit's full finding records, `FILES` = its `files`, and `ROOT`,
   `TEST_CMD`. Fixers write characterization tests before refactoring, keep behavior identical,
   edit only their files, and do not commit.
4. After the wave returns, run the test command yourself.
   - Green: `git add -A` and commit as `refactor(<scope>): <what changed> [<IDs the wave fixed>]`,
     with the scope the project uses for that area (`CONTRIBUTING.md` or `git log --oneline -20`).
   - Red: dispatch one fixer with the wave's `git diff` and the failing output, asking it to repair
     the breakage without widening the scope. Still red: `git checkout -- <wave files>`, delete the
     files the wave created, mark the wave's units SKIPPED, and go on.
5. After the last wave, run the tests once more and report: a table of unit, finding IDs, FIXED or
   SKIPPED with the fixer's reason, the commits made, and the branch. Suggest
   `/ingvarch:code-quality --changed` to audit the branch again, then the merge or PR step.

Done when the report lists every unit as FIXED or SKIPPED and the tests pass on the branch.

## Red flags

| Thought | Reality |
|---|---|
| "The repository is tiny, I will review it myself" | Run the inventory and the analyzers anyway. The same pipeline every time is the point. |
| "I will fix the obvious ones while auditing" | Nothing is edited before the gate. |
| "Verification is overkill for quality findings" | Analyzers overrate severity every run. Verifiers make the report trustworthy. |
| "Let me read the raw findings to summarize" | The aggregator does that. The main context stays small. |
| "Severity HIGH because the code is ugly" | Severity comes from the table in lenses.md, not from taste. |
| "The user is away, so I will fix everything" | Unattended means stop at the gate. |
| "Tests are slow, commit without running them" | Every wave is tested before it is committed. |

## Files

| Path | Purpose |
|---|---|
| `scripts/inventory.py` | Git-tracked source files, LOC, chunks, agent count |
| `scripts/merge_findings.py` | Validate, dedupe, assign IDs; `--brief` lists findings; `--apply-verdicts` applies verifier verdicts |
| `scripts/plan_fixes.py` | Fix units with disjoint files, parallel waves |
| `scripts/test_*.py` | The scripts' tests: `python3 -m unittest discover -s skills/code-quality/scripts` |
| `references/lenses.md` | Per-principle checklists, do-not-flag rules, severity tables |
| `references/analyzer-prompt.md` | Analyzer prompt and findings JSON schema |
| `references/verifier-prompt.md` | Refuting verifier prompt and verdict schema |
| `references/aggregator-prompt.md` | Report writer prompt |
| `references/fixer-prompt.md` | Fixer prompt with behavior-preservation rules |
| `references/report-template.md` | Structure of `report.md` |

## NEVER

- Analyze code in the main thread, even in a small repository.
- Edit a source file before the gate.
- Report a finding without quoted evidence.
- Commit a wave whose tests did not pass.
