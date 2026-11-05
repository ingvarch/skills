# skills

Ingvar's agent skills for Claude Code, packaged as one plugin. The repository is a marketplace:
add it once and every skill installs together. In Claude Code a skill runs as
`/ingvarch:<name>`.

## Skills

Git:

- [git-commit](skills/git-commit/SKILL.md): prints a one-line conventional commit command for the
  current changes. Runs only when you type it.
- [git-pr](skills/git-pr/SKILL.md): prepares a pull request: a conventional title, a body from the
  repository's template, labels and a merge method, printed as commands.

Repository:

- [repo-tidy](skills/repo-tidy/SKILL.md): docs in `docs/` under kebab-case names, the README as a
  short entry page, `AGENTS.md` as the agent file, and GitHub milestones with issues for the plan.
- [repo-settings](skills/repo-settings/SKILL.md): the About, merge methods and auto-merge, a ruleset
  on the default branch, labels, Dependabot, unused tabs off, and the community standards of a
  public repository.

## Installation

```
/plugin install ingvarch --marketplace ingvarch/skills
```

Or in two steps:

```
/plugin marketplace add ingvarch/skills
/plugin install ingvarch@ingvarch-skills
```

## Adding a skill

1. Put it in `skills/<name>/SKILL.md`, with its files beside it. The name starts with the area it
   works on: `git-`, `repo-`.
2. Write it in the shape of the others: one paragraph on what it does and who runs the commands,
   then numbered steps, each ending on a check that tells the step is done; `NEVER` last, for hard
   limits only. A skill that runs only when typed sets `disable-model-invocation: true`.
3. List it under Skills above.
4. Bump `version` in `.claude-plugin/plugin.json`: `/plugin update` installs a new version only.
5. Run `claude plugin validate .` and the tests.

Local run without installing: `claude --plugin-dir .`

## Tests

```
python3 -m unittest discover -s skills/repo-tidy/scripts
```
