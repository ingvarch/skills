# Contributing to <Name>

Thanks for helping. This file explains how to report problems and how to send a change.

## Report a bug or ask for a feature

Open an issue with one of the [issue templates](https://github.com/<owner>/<repo>/issues/new/choose).
For a bug, include <what a bug report needs: what you did, what happened and what you expected>.

Do not report security problems in public issues. See [SECURITY.md](SECURITY.md).

## Set up

Local setup and the checks are described in [docs/development.md](https://github.com/<owner>/<repo>/blob/main/docs/development.md).

## Make a change

1. Create a branch from `main` named `<type>/<short-name>`, for example `<fix/an-example>`.
2. Write a failing test that describes the behavior you want, then the code that makes it pass.
3. Run the [checks](https://github.com/<owner>/<repo>/blob/main/docs/development.md#checks). The output must have no warnings and no failures.
4. Update the files in `docs/` if the change alters what users or operators see.
5. Commit with a [conventional commit](https://www.conventionalcommits.org/) message:
   `type(scope): description`, imperative, lower case.
   - Types: `feat`, `fix`, `refactor`, `docs`, `chore`.
   - Scopes: <this project's scopes>.
6. Open a pull request and fill in the template. Link the issue it closes with `Closes #N`.

Pull requests are merged with rebase or squash, so `main` keeps a linear history.

The rules for agents working in this repository are in [AGENTS.md](https://github.com/<owner>/<repo>/blob/main/AGENTS.md).

## Code of conduct

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions are licensed under the [<License>](https://github.com/<owner>/<repo>/blob/main/LICENSE).
