# Community standards

Fill every item of GitHub's community profile (Insights, then Community standards). The templates
are in `<skill>/templates/`: copy each one, then replace every `<placeholder>` with this project's
facts (name, commands, checks, commit scopes, what a bug report needs).

## 1. Check

- `gh api 'repos/{owner}/{repo}/community/profile' --jq '{health_percentage, files: (.files | map_values(. != null))}'`
- `ls SECURITY.md .github/SECURITY.md .github/ISSUE_TEMPLATE`: the profile API leaves out the
  security policy, and it reports issue forms (`.yml`) as missing even when GitHub counts them.

## 2. Fill the gaps

Keep a file that exists; correct its stale facts.

- `LICENSE`: ask the user which license. The text is `gh api licenses/<key> --jq .body`, with the
  year and the owner's name filled in.
- `CODE_OF_CONDUCT.md`: Contributor Covenant 3.0. Reports go to the private advisory
  form `https://github.com/<owner>/<repo>/security/advisories/new`.
- `SECURITY.md`: supported versions (the latest release, or the latest commit on the default branch
  when there are no releases), how to report through the same advisory form, what to include and
  what happens next. Turn the form on:
  `gh api -X PUT 'repos/{owner}/{repo}/private-vulnerability-reporting'`.
- `CONTRIBUTING.md`: how to report a bug, the setup through the development guide
  (`docs/development.md`, or the README section when there is no guide), the steps of a
  change (branch name, test first, the checks, docs, conventional commits with this project's
  scopes, the PR template and `Closes #N`), the code of conduct and the license.
- `.github/ISSUE_TEMPLATE/`: issue forms `bug_report.yml` and `feature_request.yml` with the fields
  this project's reports need and labels from `gh label list`, and `config.yml` that turns blank
  issues off and links to the advisory form for security reports.
- `.github/pull_request_template.md`: What changes, Issues, and a checklist with this project's
  checks. The git-pr skill builds the PR body from it.
- The README gets its `## License` and `## Contributing` sections.

## 3. Done

The step 1 check prints `health_percentage` 100, the security policy and the issue forms exist, and
`gh api 'repos/{owner}/{repo}/private-vulnerability-reporting'` prints `{"enabled":true}`.
