---
name: repo-tidy
description: Tidy a repository's docs, settings and plan - every doc in docs/ under lower-case kebab-case names, the README as a short entry page with badges and a documentation index, AGENTS.md as the agent file, the GitHub settings through repo-settings, and GitHub milestones with issues for the work done and left. Use when the user asks to reorganize or clean up docs, restyle the README, or set up milestones and issues.
---

# repo-tidy

Bring a repository to one shape: the README is an **entry page**, every other doc lives in `docs/`
under a lower-case kebab-case name, agent instructions live in `AGENTS.md`, the GitHub settings
follow the repo-settings skill, and the plan lives in GitHub milestones.

`<skill>` below is this skill's folder, the base directory shown when it loads. Run its scripts from
the repository root with `python3 -I`.

Commits follow the user's instructions: run `git commit` when they asked you to commit, print the
commands otherwise.

## 1. Survey

- Work on a branch; from the default branch, create `docs/reorganize`.
- Run `python3 -I <skill>/scripts/check_docs.py`: it lists doc names to fix and links that point
  nowhere.
- Read the README and every doc. When the project is deployed, open its live URL: docs often still
  say "not deployed yet".
- Done when you hold two tables: every doc file with its new path (or **tool-required**, when a tool
  needs the name as it is), and every README section with its **home** (a guide in `docs/` or the
  entry page).

## 2. Names

- Docs (`*.md`, `*.rst`, `*.adoc` anywhere, `*.txt` at the root, everything in `docs/`): lower-case
  ASCII words joined by hyphens: `spec.md`, `smoke-test.md`, `product.md`. Abbreviations become
  words: `M2.md` becomes `milestone-2.md`.
- Code and test fixtures follow their language: Python and Rust modules with underscores, Swift and
  Java types in PascalCase.
- Tool-required names stay. `check_docs.py` already skips the common ones (`README.md`, `CLAUDE.md`,
  `AGENTS.md`, `LICENSE`, `SKILL.md`, mdBook's `SUMMARY.md`, `CMakeLists.txt`, `.github/`, a
  static-site generator's `_config.yml`). Mark any other name a tool needs as tool-required in the
  table: GitHub and agents look up names, migration tools record applied migration names and run a
  renamed one again, build tools read fixed names.
- A doc that a tool reads, such as impeccable's `PRODUCT.md` and `DESIGN.md`: confirm the tool still
  finds the new path and name before you move it. macOS file systems ignore case, so a local run
  passes even where Linux would fail; look up the names the tool accepts in its docs or its binary
  (`strings <binary> | grep -i product`). Impeccable accepts `docs/product.md` and `docs/design.md`.

## 3. Move

- `git mv` each file. A folder whose name changes only in case moves through a temporary name:
  `git mv ADR adr-tmp && git mv adr-tmp adr`.
- Update every reference: grep the whole repository for each old name, code comments and the old
  README's links included. Links inside `docs/` are relative to `docs/`: `spec.md`, `../README.md`.
- Agent file: each `CLAUDE.md` (the root and any subfolder) becomes `AGENTS.md`, and a new
  `CLAUDE.md` beside it holds the single line `@AGENTS.md`. Claude Code imports the file through
  that line in every version and on every platform; other agents read `AGENTS.md` directly. Run
  `git mv CLAUDE.md AGENTS.md`, then write the new `CLAUDE.md`. When an `AGENTS.md` exists already,
  merge the rules of `CLAUDE.md` into it instead. References to `CLAUDE.md` now point to
  `AGENTS.md`.
- Done when grep finds no old name, apart from tool boilerplate that names a file generically.
- Commit the renames with their references.

## 4. Guides

Move the README's how-to sections into guides in `docs/`. Each guide opens with one line on what it
covers and a link to its neighbour.

- `development.md`: Prerequisites, Local secrets, Local database, Run, Checks, Project structure.
- `deployment.md`: Resources, Configuration (the settings table), Secrets, Deploy, operations such as
  logs or opt-outs, Before launch.
- `api.md`, `architecture.md`, `limits.md`, `admin.md` when the repository has that material.

Move the text, drop emoji, and write the few joining sentences in plain language. Correct claims
that went stale. Done when every section of the old README has a home: compare them section by
section.

## 5. Entry page

```markdown
# <Name>

<badges, one per line>

<One paragraph: what it is, who it is for, what they get, and who makes it.>

## Features

<5 to 7 bullets a user cares about>

## Usage

<A deployed service: its URL and one request. A CLI or library: the install command and one call.
Leave the section out when nothing is deployed or published.>

## Quick start

You need <tools>, see [docs/development.md](docs/development.md).

<4 to 6 commands; the last one shows it works>

## Documentation

- [<Title>](docs/<file>.md): <what it covers, as a short list>

## License        <- only when LICENSE exists
## Contributing   <- only when CONTRIBUTING.md exists
```

Badges, each one true for this repository:

- CI: one per workflow that runs on push to the default branch:
  `[![CI](https://github.com/<owner>/<repo>/actions/workflows/<file>/badge.svg)](https://github.com/<owner>/<repo>/actions/workflows/<file>)`
- Live site: `[![<host>](https://img.shields.io/website?url=<url-encoded health URL>&label=<host>)](<url>)`
- Language and platform:
  `[![TypeScript](https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white)](tsconfig.json)`;
  Rust is `Rust-dea584` with `logo=rust&logoColor=black`; Cloudflare Workers is
  `Cloudflare%20Workers-f38020` with `logo=cloudflare&logoColor=white`.
- Release (`img.shields.io/github/v/release/<owner>/<repo>`) when `gh release list --limit 1` shows
  one, and license (`img.shields.io/github/license/<owner>/<repo>`) when
  `gh repo view --json licenseInfo` names one. Both need a public repository: shields.io cannot read
  private ones.

Point `AGENTS.md` at the docs: one line per doc and when to read it.

## 6. Repository settings

Run the repo-settings skill. Its files go on this branch.

## 7. Verify

- `check_docs.py` reports 0 links, and no names apart from the tool-required ones in the step 1
  table.
- The project's own checks pass: code comments changed too.
- Commit the guides, the entry page and the agent file.

## 8. Milestones and issues

Offer to put the plan into GitHub: milestones, the done work as closed issues linked to the PRs that
delivered it, and the open work as issues. On a yes, follow [milestones.md](milestones.md) before
the PR, so the PR can close its own issue.

## 9. Pull request

Prepare it with the git-pr skill. With step 8 done, the body says `Closes #<docs issue>` and the
`gh pr create` command carries `--milestone`.
