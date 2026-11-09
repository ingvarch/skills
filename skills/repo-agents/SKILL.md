---
name: repo-agents
description: Bring a repository's agent instructions to one shape - AGENTS.md with a CLAUDE.md beside it that imports it, a line for every doc that says when to read it, the commands that take more than one lookup to find, and the rules the code does not show. Use when the user asks to write, check or update AGENTS.md or CLAUDE.md, or to make a repository easier for agents to work in.
---

# repo-agents

Bring a repository's agent file to one shape: the rules live in `AGENTS.md`, and a `CLAUDE.md` beside
it imports them. The file is a set of pointers for an agent that starts with no context: what the
repository is, which doc to read before which task, and the rules it cannot find by looking. The
root file loads in every session, so every line costs context in every session.

`<skill>` below is this skill's folder, the base directory shown when it loads. Run its script from
the repository root with `python3 -I`. Files go on the current branch; on the default branch, create
`docs/agents-md` first. Commits follow the user's instructions: run `git commit` when they asked you
to commit, print the commands otherwise.

## 1. Survey

- Run `python3 -I <skill>/scripts/check_agents.py`. It prints `agent:` for an agent file that is
  missing, is a symlink, misses the import of `AGENTS.md` or holds an `@path` import other agents
  cannot follow; `doc:` for a doc that no `AGENTS.md` links to; and `link:` for a link in an agent
  file that points nowhere.
- Read every `AGENTS.md` and `CLAUDE.md`, the README, `CONTRIBUTING.md`, and every doc that the
  script lists or the agent files link to.
- Find what the project runs: the workflows in `.github/workflows/`, the scripts in `package.json`,
  `Makefile`, `pyproject.toml` or `Cargo.toml`, and the setup sections of the docs.
- Done when you hold a table of every doc, with what it covers and the task before which an agent
  reads it or why no agent task needs it, and of every folder with an agent file, marked as agent
  instructions or as a template or fixture that stays as it is.

## 2. Agent files

Every folder with agent instructions holds `AGENTS.md` with the rules and a `CLAUDE.md` with the line
`@AGENTS.md`. Other agents read `AGENTS.md`. Claude Code reads `CLAUDE.md`, and falls back to
`AGENTS.md` only when no `CLAUDE.md` exists and only from version 2.1.277; the import gives every
version the same rules.

- A symlink: writing through it overwrites its target, so `git rm` the link first. When it pointed
  at the other agent file, that file becomes `AGENTS.md` (`git mv CLAUDE.md AGENTS.md` when it is
  `CLAUDE.md`). When it pointed at another tool's file, such as `.cursorrules`, copy the rules into
  `AGENTS.md` and leave that file to its tool. Then write `CLAUDE.md`.
- Only `CLAUDE.md`: `git mv CLAUDE.md AGENTS.md`, then write a new `CLAUDE.md` with the line
  `@AGENTS.md`.
- Both, and `CLAUDE.md` holds rules: merge them into `AGENTS.md` and keep the import. A rule that
  only Claude Code can follow, such as one that names a Claude Code skill or slash command, stays in
  `CLAUDE.md` below the import.
- `.claude/CLAUDE.md`: Claude Code reads it as a second root `CLAUDE.md`; treat one in a subfolder
  as a second `CLAUDE.md` of the folder above. Merge its rules into that folder's `AGENTS.md` the
  same way, then `git rm` it.
- Only `AGENTS.md`: write the `CLAUDE.md`.
- Neither, at the root: create both; step 3 fills `AGENTS.md`.
- An `@path` import anywhere in `AGENTS.md`: only Claude Code follows it. Turn it into a doc line
  for step 3, or move the rules it holds into `AGENTS.md`. An import of a personal file
  (`@~/...`) goes back to `CLAUDE.md`.
- References that mean the project's agent rules ("see CLAUDE.md") point at `AGENTS.md`. References
  to the `CLAUDE.md` file itself stay: imports, tool configuration, file lists such as `.gitignore`.

Done when the script prints no `agent:` line apart from the template and fixture folders in the
step 1 table, and grep for `CLAUDE.md` finds only references to the file itself.

## 3. Write AGENTS.md

The root file:

```markdown
# AGENTS.md

<One paragraph: what the repository is, its main parts, and the rules every change follows.>

- [<path>](<path>): read before <task>. It has <what it covers, as a short list>.

## Commands    <- only commands that take more than one lookup to find

## Rules       <- only rules that no doc and no config holds
```

- Docs: one line per doc, and the line is its pointer. `read before <task>` names the task that
  sends an agent to the doc, so it reads the doc when that task comes and skips it otherwise. Link a
  section when only that section serves the task (`docs/development.md#checks`). A folder of docs of
  one kind, such as ADRs, gets one line for the folder.
- Commands: build, test and lint commands live in `package.json`, the `Makefile` and the CI
  workflow, where an agent finds them in one lookup and where they stay current. List a command here
  only when finding it takes more: which of many scripts CI runs, a variable it needs, an order that
  matters. Run each command you list and fix or drop the ones that fail. For a command that does not
  exit, such as a dev server or a watcher, check that it starts, then stop it.
- Rules: what an agent cannot find by looking, such as an unwritten convention, the reason behind a
  choice, or a trap. Take rules from the existing agent files, the docs and the user; add one only
  from a source you can name. Drop a rule that a linter, a test or a config enforces, one an agent
  follows anyway ("write clean code"), and one that went stale. When a doc holds the rule, link the
  doc.
- A subfolder `AGENTS.md` holds only the rules for that folder: Claude Code loads it once it works on
  a file there.
- Each file stays under 200 lines, the size Claude Code's docs recommend; shorter is better.
- Plain words, no emoji.

Done when, for every `AGENTS.md` outside the template and fixture folders in the step 1 table, every
line below the opening paragraph links a doc, gives a command, or states a rule that the repository
holds nowhere else, `wc -l` shows it under 200 lines, and the script prints no `link:` line for it;
and the script prints `doc:` lines only for the docs that the step 1 table leaves out.

## 4. Report

- Show the user each changed agent file and a list: docs linked, commands fixed or dropped, rules
  moved, merged or dropped with the reason for each drop, and the docs left out with the reason.
- Commit the agent files and the references you changed.

Done when the user has the list, and the commit or its commands.

## NEVER

- NEVER run a command that deploys, publishes, migrates a database or deletes data to check it:
  compare it with the CI workflow and the scripts instead.
- NEVER drop a rule without listing it and its reason in step 4.
