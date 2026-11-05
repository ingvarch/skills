# skills

[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757?logo=claude&logoColor=white)](https://code.claude.com/docs/en/plugins)
[![Python](https://img.shields.io/badge/Python-3776ab?logo=python&logoColor=white)](skills/repo-tidy/scripts)
[![License](https://img.shields.io/github/license/ingvarch/skills)](LICENSE)

Agent skills for Claude Code, packaged as one plugin, for a maintainer who wants every GitHub
repository in one shape: conventional commits and pull requests, docs in `docs/` behind a short
README, the same GitHub settings, and the plan in milestones. One install brings every skill, and
each runs as `/ingvarch:<name>`. Made by Igor Churmeev ([ingvarch](https://github.com/ingvarch)).

## Features

- **git-commit**: prints a one-line conventional commit command for the current changes. Runs only
  when you type it.
- **git-pr**: prepares a pull request: a conventional title, a body from the repository's template,
  labels and a merge method, printed as commands.
- **repo-tidy**: docs in `docs/` under kebab-case names, the README as a short entry page,
  `AGENTS.md` as the agent file, and GitHub milestones with issues for the plan.
- **repo-settings**: the About, merge methods and auto-merge, a ruleset on the default branch,
  labels, Dependabot, unused tabs off, and the community standards of a public repository.
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
claude --plugin-dir . plugin details ingvarch
```

## Documentation

- [Development](docs/development.md): prerequisites, running from a checkout, checks, project
  structure, adding a skill, the skill shape and releases.

## License

[MIT](LICENSE).

## Contributing

Bug reports, ideas and pull requests are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).
