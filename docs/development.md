# Development

How to run the plugin from a checkout, check it, add a skill and release a version. What the skills
do and how to install them is in the [README](../README.md).

## Prerequisites

- [Claude Code](https://code.claude.com/docs/en/setup).
- Python 3.9 or newer, for the scripts in `skills/*/scripts/`.
- [GitHub CLI](https://cli.github.com/) `gh`, logged in, to try the `git-` and `repo-` skills on a
  real repository.

## Run

```
claude --plugin-dir .
```

Claude Code starts with the plugin from the working tree. The skills run as `/ingvarch:<name>`.

## Checks

```
claude plugin validate .
python3 -m unittest discover -s skills/repo-tidy/scripts
python3 -m unittest discover -s skills/code-quality/scripts
python3 -I skills/repo-tidy/scripts/check_docs.py
claude --plugin-dir . plugin details ingvarch
```

The first prints `Validation passed`, the tests end with `OK`, `check_docs.py` finds 0 names and 0
links, and `details` lists every skill in `skills/`.

## Project structure

```
.claude-plugin/
  marketplace.json   the marketplace ingvarch-skills with one plugin, ingvarch, at the root
  plugin.json        the plugin's name, version and description
skills/<name>/
  SKILL.md           the skill
  *.md, *.json       files the skill reads on demand
  scripts/           scripts the skill runs, with their tests (test_*.py)
  references/        files the skill reads on demand, when it has many
  templates/         files the skill copies into a repository
docs/                this guide
```

Claude Code finds every skill in `skills/` on its own: `plugin.json` does not list them.

## Adding a skill

1. Put it in `skills/<name>/SKILL.md`, with its files beside it. The name starts with the area it
   works on: `git-` for history, commits and pull requests, `repo-` for a repository's docs and
   settings, `code-` for the code itself, `session-` for the work of the current session.
2. Write it in the [skill shape](#skill-shape).
3. A script starts with a failing test in `scripts/test_<script>.py`. The skill runs it from the
   repository root with `python3 -I`. A new `scripts/` folder gets its test command in the
   [checks](#checks).
4. List the skill in the [README](../README.md#features), and in the skill dropdown of
   `.github/ISSUE_TEMPLATE/bug_report.yml`.
5. Run the [checks](#checks), then [release](#release).

## Skill shape

- Frontmatter: `name` equal to the folder name, and a `description` that says what the skill does
  and when to use it. A skill that runs only when typed sets `disable-model-invocation: true`.
- One paragraph on what the skill does and who runs the commands: the agent, or the user from
  printed commands.
- Numbered steps, each ending on a check that tells the step is done.
- `NEVER` last, for hard limits only.
- Reference material that only some runs need goes into a file beside `SKILL.md`, or into
  `references/` when there are many, behind one line that says when to read it.

## Release

Users get a change only with a new version. Bump `version` in `.claude-plugin/plugin.json`: the
patch number for a fix, the minor number for a new skill or a change in what a skill does. After the
merge, users update with:

```
claude plugin marketplace update ingvarch-skills
claude plugin update ingvarch@ingvarch-skills
```

and restart Claude Code.
