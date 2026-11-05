---
name: repo-settings
description: Bring a GitHub repository's settings to one shape - the About, merge methods and auto-merge, a ruleset on the default branch, a standard label set, Dependabot and secret scanning, unused tabs turned off, and a full community profile for a public repository. Use when the user asks to set up, check or align a repository's GitHub settings, labels, branch protection or community standards.
---

# repo-settings

Bring a GitHub repository's settings to one shape.

`<skill>` below is this skill's folder, the base directory shown when it loads. The files it adds
come from `<skill>/templates/`: a template goes to the same path in the repository, and
`templates/github/` goes to `.github/`. Run every command from the repository root: `gh` fills
`{owner}` and `{repo}` from it. API calls change the live repository at once. Files go on the
current branch; on the default branch, create `chore/repo-settings` first. Commits follow the
user's instructions: run `git commit` when they asked you to commit, print the commands otherwise.

## 1. Survey

- `gh repo view --json visibility,description,homepageUrl,repositoryTopics,defaultBranchRef`
- `gh api 'repos/{owner}/{repo}' --jq '{allow_auto_merge, delete_branch_on_merge, allow_update_branch, allow_merge_commit, allow_squash_merge, allow_rebase_merge, squash_merge_commit_title, has_wiki, has_projects, security_and_analysis}'`
- `gh api 'repos/{owner}/{repo}/rulesets'` and `gh label list --limit 200`

On a private repository of a free account GitHub refuses auto-merge and rulesets. Note each
refusal and tell the user at the end; the other steps still apply.

## 2. About

The description is one sentence of at most 350 characters: what the project is and who it is for,
taken from the README's opening paragraph. The website is the live URL, or none when nothing is
deployed. Topics are 5 to 10 words a user would search for (language, platform, kind of tool),
lower-case and hyphenated. Keep the current values that still fit. Show the three and apply them on
a yes: `gh repo edit --description "<sentence>" --homepage "<url>" --add-topic <a>,<b>`; drop stale
topics with `--remove-topic`.

## 3. Merging

```
gh repo edit --enable-merge-commit=false --enable-squash-merge --squash-merge-commit-message pr-title \
  --enable-rebase-merge --enable-auto-merge --delete-branch-on-merge --allow-update-branch
```

The default branch keeps a linear history of conventional commits: a squash takes the PR title,
which the git-pr skill writes as a conventional commit.

## 4. Ruleset

One ruleset on the default branch: no deletion, no force push, linear history, and the required
checks, so auto-merge has something to wait for. The repository admin bypasses it and can still
push directly.

- Required checks are the jobs of workflows that run on every pull request: `on: pull_request` with
  no `paths`, `paths-ignore` or `branches` filter that skips some. A required check that does not run
  blocks the merge forever. Take each name exactly as a recent PR shows it:
  `gh pr checks <number> --json name,workflow`.
- Copy `<skill>/ruleset.json` to the scratchpad and list the checks in `required_status_checks`.
  Without CI, drop the `required_status_checks` rule.
- Create it: `gh api -X POST 'repos/{owner}/{repo}/rulesets' --input <file>`. When a ruleset named
  `default-branch` exists, update it: `gh api -X PUT 'repos/{owner}/{repo}/rulesets/<id>' --input <file>`.
  Leave other rulesets and classic branch protection as they are, and mention them to the user.

## 5. Labels

`<skill>/labels.json` holds the standard set: issue types, `dependencies`, `security`, `tech-debt`,
`blocked` and GitHub's defaults. A label that means the same under another name (`feature`, `docs`)
gets renamed first, so its issues keep it: `gh label edit <old> --name <new>`. Then create or update
the set:

```
jq -r '.[] | [.name, .color, .description] | @tsv' <skill>/labels.json |
  while IFS=$'\t' read -r name color description; do
    gh label create "$name" --color "$color" --description "$description" --force
  done
```

Project labels, such as areas named after commit scopes, stay.

## 6. Dependabot and secret scanning

- Alerts, then security updates:
  `gh api -X PUT 'repos/{owner}/{repo}/vulnerability-alerts'` and
  `gh api -X PUT 'repos/{owner}/{repo}/automated-security-fixes'`.
- `.github/dependabot.yml` from the template: one entry per package ecosystem this repository has,
  plus `github-actions` when `.github/workflows/` exists. Labels: `dependencies` and an area label
  when the project has one. Commit prefix: `chore(<scope>)` with the project's scope for builds or
  CI.
- `.github/release.yml` from the template when the repository publishes GitHub releases
  (`gh release list --limit 1`): release notes then group by label. Maintenance gets the project's
  area labels for builds, CI and tests, or none.
- Public repository: `gh repo edit --enable-secret-scanning --enable-secret-scanning-push-protection`.

## 7. Tabs

- Wiki off when it has no pages: `git ls-remote https://github.com/<owner>/<repo>.wiki.git` fails,
  then `gh repo edit --enable-wiki=false`.
- Projects off when none is linked:
  `gh api graphql -F owner='{owner}' -F name='{repo}' -f query='query($owner:String!,$name:String!){repository(owner:$owner,name:$name){projectsV2(first:1){totalCount}}}'`
  prints 0, then `gh repo edit --enable-projects=false`. The query needs the `read:project` scope;
  when gh lacks it, ask the user to run `! gh auth refresh -s read:project`.

## 8. Community standards

For a public repository, follow [community.md](community.md).

## 9. Check

Commit the files from steps 6 and 8. Then every value below holds, or the user knows why not:

- `gh api 'repos/{owner}/{repo}' --jq '{allow_auto_merge, delete_branch_on_merge, allow_update_branch, allow_merge_commit, squash_merge_commit_title, has_wiki, has_projects}'`:
  `true`, `true`, `true`, `false`, `"PR_TITLE"`, and the tabs as step 7 decided.
- `gh api 'repos/{owner}/{repo}/automated-security-fixes'` prints `"enabled":true`.
- The ruleset is active and its bypass actor is the admin role:
  `gh api graphql -F owner='{owner}' -F name='{repo}' -f query='query($owner:String!,$name:String!){repository(owner:$owner,name:$name){rulesets(first:10){nodes{name enforcement bypassActors(first:5){nodes{repositoryRoleName bypassMode}}}}}}'`
  shows `default-branch`, `ACTIVE` and `admin`.
- `gh label list --limit 200` has every label from `labels.json`.
- Public repository: the checks in community.md pass, and
  `security_and_analysis` shows secret scanning and push protection `enabled`.
