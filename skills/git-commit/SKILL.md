---
name: git-commit
description: Print a one-line conventional commit command for the current changes. Prints the command; never runs git add or git commit.
disable-model-invocation: true
---

# git-commit

Print the commit command for the current changes. The maintainer runs it; you only print it.

## 1. Read the changes

`git diff --staged`. When nothing is staged, `git status --short` and `git diff`: the command then
stages the files first.

## 2. Message

`type(scope): description`, imperative, lower case, no period.

- Type: `feat` a new feature, `fix` a bug fix, `refactor` a code change that keeps behavior, `docs`
  documentation, `chore` maintenance.
- Scope: the area changed, named as the project names it: the scopes in `CONTRIBUTING.md` or in
  `git log --oneline -20` (`api`, `ui`, `auth`).
- Description: what the change does, in a few words.

## 3. Print the command

Print only the command:

```fish
git commit -m "<message>"
# or, when nothing is staged:
git add <files> && git commit -m "<message>"
```

## NEVER

- Run `git add` or `git commit` yourself, or ask for permission to run them. Print them.
