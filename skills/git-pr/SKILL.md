---
name: git-pr
description: Prepare a GitHub pull request for the current branch in the maintainer's name - a conventional-commit title, a body from the repository's PR template, the labels (required), and a merge method (rebase and merge or squash) with the reason. Prints the commands to run; never pushes or creates the PR itself. Use when a piece of work is finished and committed, or when the user asks for a PR.
---

# git-pr

Prepare a pull request for the current branch. The maintainer runs the commands; you only print them.

## 1. Check the branch

- Base branch: `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.
- If the current branch is the base branch, stop and print the command that creates a branch, named
  `<type>/<short-name>` (`feat/api-types`, `fix/vultr-zones`): `git switch -c feat/api-types`.
- If `git status --short` shows changes that belong to the PR, stop and ask the maintainer to commit them with
  `/ingvarch:git-commit`.
- `git log --oneline <base>..HEAD` lists the commits the PR carries. Read them; the title, the body and the merge
  method depend on them.

## 2. Title

One conventional commit line: `type(scope): description`, imperative, lower case, no period. For a PR of one commit,
use that commit's title.

## 3. Body

Use the repository's template: `.github/pull_request_template.md`, or `.github/PULL_REQUEST_TEMPLATE.md`, `docs/` or
the root. Keep its headings and checklist, and drop the HTML comment. Without a template, use `## What changes` and
`## Checklist`.

- **What changes:** what the change does for someone using the project, and why. Then the notable details as a short
  list, bugs found and fixed along the way, and things found and left for later. Plain words, each thing said once.
- **Issues:** `Closes #N` for every issue the PR finishes, `Part of #N` for a parent it does not finish.
- **Checklist:** tick an item only when it is true and you checked it in this session, for example `make check` ran
  green on the branch head. Leave the rest unticked and say why in your reply.

Write the body to a file: `<scratchpad>/pr-body-<branch>.md`, or `/tmp/pr-body-<branch>.md` when there is no
scratchpad.

## 4. Labels

Required: every PR gets labels. Take them only from the labels the repository has:
`gh label list --limit 100 --json name,description`.

- **Type**: one label for the kind of change, from the commit type: `feat` - `enhancement`, `fix` - `bug`, `docs` -
  `documentation`, `refactor` - `refactor`, `chore` - `chore`, a dependency update - `dependencies`. Use the
  repository's own name when it differs.
- **Area**: a label for each part of the project the PR changes, from the commit scopes and the changed files, when
  the repository has one (`ui`, `jobs`, `storage`).
- **Issues**: every label of the issues the PR closes: `gh issue view <N> --json labels --jq '.labels[].name'`.

If the repository has no label for the type of change, stop and print the command that creates it, before the PR
commands: `gh label create <name> --description "<what it marks>"`. Never put a label in `--label` that the
repository does not have; `gh pr create` fails on it.

## 5. Merge method

Pick one and give the reason in one or two sentences.

- **Rebase and merge** when every commit is a step forward that stands on its own, with the tests green at each one.
  `main` keeps the commits and their messages.
- **Squash and merge** when some commits fix earlier commits of the same branch (review fixes, fixups, "wip").
  `main` should not read "built it, broke it, fixed it" for one piece of work. The squash commit takes its message
  from the merge command below, so rewording the branch commits first is wasted work.
- **Create a merge commit:** do not recommend it; it breaks the linear history.

If a squash is needed only because of a fixup or two that could be folded into their commits, say so: the maintainer
may prefer to fold them and rebase.

## 6. Print the commands

Print, in fish syntax, and nothing else to run:

```fish
git push -u origin <branch>
gh pr create --base <base> --title "<title>" --body-file <file> --label "<label>,<label>"
```

Then the labels with the reason for each in a few words, the merge method with its reason, and the command for after
the review:

```fish
gh pr merge <number> --rebase --delete-branch
# or, for a squash with a one-line message:
gh pr merge <number> --squash --subject "<title>" --body "" --delete-branch
```

## NEVER

- Run `git push`, `gh pr create` or `gh pr merge` yourself, or ask for permission to run them. Print them.
- Print `gh pr create` without `--label`.
