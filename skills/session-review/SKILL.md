---
name: session-review
description: Have a fresh reviewer agent check the changes made in this session against the user's request and the claims made about them, verify every finding at the cited line, and report a verdict before anything is fixed. Use when the user asks to double-check, re-review or self-review the work of this session, typically after it was reported done.
argument-hint: "[focus]"
disable-model-invocation: true
---

# session-review

You wrote this code, so you are the worst person to judge it. A fresh reviewer agent judges; you
supply the facts, verify its findings and report. The code stays as it is until the user picks what
to fix.

`<skill>` below is this skill's folder, the base directory shown when it loads. Focus from the
user: `$ARGUMENTS` (may be empty).

## 1. Collect the scope

- Git repository: the changed files are `git status --porcelain` plus the commits you made this
  session. `DIFF_CMD` is `git diff HEAD`, or `git diff <base>` when you committed during the session
  (`<base>` is HEAD before your first commit). Untracked files have no diff; list them so the
  reviewer reads them whole.
- Not a git repository: list the files you created or edited this session; `DIFF_CMD` is
  `none, read the files`.
- Nothing changed: say so and stop.

Done when you hold the root, the file list and `DIFF_CMD`.

## 2. Write the brief

Fill `<skill>/reviewer-prompt.md`:

- `REQUEST`: the user's messages that define the task, verbatim, later corrections included. Never
  paraphrase: gaps between the request and the code are the most common serious findings.
- `CLAIMS`: what you told the user is done, as facts: features, "tests pass", the commands you ran
  and their results.
- `ROOT` (absolute), `FILES`, `DIFF_CMD`, `FOCUS`.

Keep out of the brief:

- Why you chose the design, why something is "fine", what is good about it. It anchors the
  reviewer.
- Problems you already suspect. Write them down for yourself and compare in step 4; the reviewer
  must find them on its own.

Done when every placeholder of the template is filled.

## 3. Dispatch

One Agent call, `subagent_type: general-purpose`, with the filled template as the prompt. Over about
1500 changed lines, or several unrelated areas: two reviewers in one message, split by files.

Done when every reviewer has replied.

## 4. Verify

Findings are claims, not verdicts. For each one, open the cited line and check that the problem is
real and belongs to this change. Mark it CONFIRMED or REJECTED with a one-line reason. Add the
suspects from your own list that the reviewer missed, labelled as yours.

Done when every finding is CONFIRMED or REJECTED.

## 5. Report, then stop

In the user's language:

1. Verdict: READY or NOT READY.
2. Refuted claims first. Each one means your earlier report was wrong; say so plainly.
3. A table of confirmed findings: #, severity, `file:line`, problem, fix.
4. Rejected findings, one line each with the reason.
5. Open questions.

Then AskUserQuestion: fix HIGH, fix HIGH and MEDIUM, pick by number, or nothing. Fixes follow TDD:
a failing test first. After fixing, run the tests again and suggest a commit message.

Done when the user has picked what to fix, and the picked fixes pass the tests.

## Common mistakes

| Mistake | Instead |
|---|---|
| Summarizing the request | Quote it verbatim |
| Explaining design choices in the brief | Facts only |
| Reviewing yourself because the diff is small | Always dispatch |
| Forwarding findings without checking | Open each cited line |
| Softening a refuted "tests pass" or "done" | Lead the report with it |

## NEVER

- Review the changes in the main thread instead of a reviewer agent.
- Change code before the user picks what to fix.
