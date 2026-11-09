# skills

[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757?logo=claude&logoColor=white)](https://code.claude.com/docs/en/plugins)
[![Python](https://img.shields.io/badge/Python-3776ab?logo=python&logoColor=white)](skills/repo-tidy/scripts)
[![License](https://img.shields.io/github/license/ingvarch/skills)](LICENSE)

Agent skills for Claude Code, packaged as one plugin, for a maintainer who wants every GitHub
repository in one shape: conventional commits and pull requests, docs in `docs/` behind a short
README and an `AGENTS.md` that points agents to them, the same GitHub settings, and the plan in
milestones. Other skills audit the code, review or hand over the work of a session, and write store
release notes. One install brings every skill, and each runs as `/ingvarch:<name>`. Made by Igor
Churmeev ([ingvarch](https://github.com/ingvarch)).

## Features

- **git-commit**: prints a one-line conventional commit command for the current changes. Runs only
  when you type it.
- **git-pr**: prepares a pull request: a conventional title, a body from the repository's template,
  labels and a merge method, printed as commands.
- **git-whats-new**: "What's New" notes for the App Store, Google Play or a changelog from the
  commits of a branch, as 3 to 6 English bullets ready to paste.
- **repo-tidy**: docs in `docs/` under kebab-case names, the README as a short entry page, the
  agent file through repo-agents, and GitHub milestones with issues for the plan.
- **repo-agents**: `AGENTS.md` with a `CLAUDE.md` that imports it, a line for every doc that says
  when to read it, and only the commands and rules an agent cannot find by looking.
- **repo-settings**: the About, merge methods and auto-merge, a ruleset on the default branch,
  labels, Dependabot, unused tabs off, and the community standards of a public repository.
- **code-quality**: a DRY, KISS, YAGNI and SOLID audit by parallel agents with a refuting verifier,
  a report of `file:line` findings, and fixes of the findings you pick on a branch, test first.
  Runs only when you type it.
- **session-review**: a fresh reviewer agent checks this session's changes against your request
  and the claims made about them, before anything is fixed. Runs only when you type it.
- **session-handoff**: writes `handoff.md`, kept out of git, so a new session can continue the work
  from that file alone.
- One marketplace: a single install brings every skill, and an update brings every change.

## Usage

```
claude plugin install ingvarch --marketplace ingvarch/skills
```

Then, in Claude Code inside a repository:

```
/ingvarch:repo-tidy
```

## Quick start

You need Claude Code and Python 3.9 or newer, see [docs/development.md](docs/development.md).

```
git clone https://github.com/ingvarch/skills.git
cd skills
claude plugin validate .
python3 -m unittest discover -s skills/repo-tidy/scripts
python3 -m unittest discover -s skills/repo-agents/scripts
python3 -m unittest discover -s skills/code-quality/scripts
claude --plugin-dir . plugin details ingvarch
```

## Documentation

- [Development](docs/development.md): prerequisites, running from a checkout, checks, project
  structure, adding a skill, the skill shape and releases.

## License

[MIT](LICENSE).

## Contributing

Bug reports, ideas and pull requests are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).
