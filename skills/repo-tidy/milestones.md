# Milestones and issues

Turn the project's plan into GitHub milestones and issues. Everyone with access to the repository
sees what you create, so show the plan and wait for a yes before step 4.

## 1. Gather

Read every source:

- The build order or roadmap in the spec: steps built and steps left.
- Merged PRs (`gh pr list --state merged --limit 1000 --json number,title,body`), and for work
  pushed without a PR, its commit (`git log --oneline`).
- Checklists (`- [ ]`) and sections such as open questions, still to verify, before launch and left
  for later, in the docs and in PR bodies.
- `TODO` and `FIXME` in the code.
- Existing issues and milestones, to reuse:
  `gh issue list --state all --limit 1000 --json number,title,state,milestone,labels` and
  `gh api 'repos/{owner}/{repo}/milestones?state=all'`.
- The next milestone's doc: its build steps and its open questions.

Done when every item from every source maps to an issue or to a reason to leave it out.

## 2. Plan

- Milestones in the project's own words ("M1: MVP", "M2: Monitoring, accounts and badge"), each with
  one sentence that names the doc specifying it.
- One issue per build step or open item. Title: an imperative for work ("Probe the Cloudflare Email
  Routing DKIM selector"). Body: the facts with the doc section they come from, and a checklist
  when the issue has parts.
- Each open question gets its own `question` issue, titled as a question ("Apex to www redirect:
  keep it a pass?"), in the milestone where it must be answered. The step it blocks lists it as
  `- [ ] {issue:<key>}`, so the question comes earlier in the plan.
- Done work: one closed issue per step, `done` set to the PR (`#12`) or the commit SHA that delivered
  it. Done issues come first, so the numbers follow history.
- One issue for the docs work itself; the docs PR closes it.
- Labels only from `gh label list`. Type: feature `enhancement`, decision `question`, docs, copy and
  legal text `documentation`, operations and checks on live systems `chore`, defect `bug`. When the
  repository lacks a type label, ask to create it:
  `gh label create chore --description "Maintenance, config and tooling"`.
- Merged PRs join the milestone they delivered.

## 3. Show

Write the plan to `<scratchpad>/issues-plan.json` and run
`python3 -I <skill>/scripts/issues.py <scratchpad>/issues-plan.json --dry-run`. It stops on a label
the repository lacks, a closed milestone, a reused key or a placeholder that points forward. Show
the user the milestones and, per milestone, the issue titles with labels and state. Wait for a yes.

## 4. Create

`python3 -I <skill>/scripts/issues.py <scratchpad>/issues-plan.json`. After any failure, run it
again: it reuses the milestones and issues that exist, moves them into their planned milestone and
closes the done ones.

## 5. Check

- Counts per milestone:
  `gh api 'repos/{owner}/{repo}/milestones?state=all' --jq '.[] | "\(.title): \(.open_issues) open, \(.closed_issues) closed"'`
  (merged PRs count among the closed).
- No duplicate titles:
  `gh issue list --state all --limit 1000 --json title --jq '[.[].title] | group_by(.) | map(select(length > 1))'`
  prints `[]`.

## Plan format

```json
{
  "repo": "owner/name",
  "milestones": [{"title": "M1: MVP", "description": "The MVP: a public passive scanner (docs/spec.md)."}],
  "issues": [
    {"key": "scaffold", "title": "Scaffold the Worker", "body": "Build order step 1 in docs/spec.md section 14.",
     "milestone": "M1: MVP", "done": "ba0e846"},
    {"key": "dkim", "title": "Probe the Cloudflare Email Routing DKIM selector", "body": "...",
     "milestone": "M1: MVP", "labels": ["enhancement"]},
    {"key": "own-domain", "title": "vardis.is scores A in Netskor", "body": "- [ ] DKIM ({issue:dkim})",
     "milestone": "M1: MVP", "labels": ["chore"]}
  ],
  "pull_requests": [{"number": 1, "milestone": "M1: MVP"}]
}
```

- `done` closes the issue and ends its body with "Done in <ref>."; a `#N` there shows on that PR's
  timeline.
- `{issue:<key>}` becomes the number of an issue earlier in the plan.
- The title identifies an issue between runs, so keep titles stable once created.
