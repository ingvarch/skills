# Contributing to skills

Thanks for helping. This file explains how to report problems and how to send a change.

## Report a bug or ask for a feature

Open an issue with one of the [issue templates](https://github.com/ingvarch/skills/issues/new/choose).
For a bug, include the skill, the message you typed, what the agent did and what you expected.

Do not report security problems in public issues. See [SECURITY.md](SECURITY.md).

## Set up

Local setup, the checks and the shape of a skill are described in
[docs/development.md](docs/development.md).

## Make a change

1. Create a branch from `main` named `<type>/<short-name>`, for example `fix/git-pr-labels`.
2. A change to a script under `skills/*/scripts/` starts with a failing test that describes the
   behavior you want, then the code that makes it pass. A skill file follows the
   [skill shape](docs/development.md#skill-shape).
3. Run the [checks](docs/development.md#checks). The output must have no failures.
4. Bump `version` in `.claude-plugin/plugin.json` when the change reaches users, and list a new
   skill in the [README](README.md#features).
5. Commit with a [conventional commit](https://www.conventionalcommits.org/) message:
   `type(scope): description`, imperative, lower case.
   - Types: `feat`, `fix`, `refactor`, `docs`, `chore`.
   - Scopes: the skill's name (`git-pr`, `repo-tidy`), `plugin` for `.claude-plugin/`, or `repo`
     for the README, `docs/`, the community files and `.github/`.
6. Open a pull request and fill in the template. Link the issue it closes with `Closes #N`.

Pull requests are merged with rebase or squash, so `main` keeps a linear history.

The rules for agents working in this repository are in [AGENTS.md](AGENTS.md).

## Code of conduct

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
