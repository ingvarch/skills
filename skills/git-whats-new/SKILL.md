---
name: git-whats-new
description: Write "What's New in This Version" release notes for the App Store, Google Play or a changelog from the user-visible changes on the current branch or in the last N commits - 3 to 6 short English bullets in one block ready to paste. Use when the user asks for release notes, store notes or what's new in a version.
argument-hint: "[N]"
---

# git-whats-new

Turn the commits of a release into 3 to 6 bullets that a user of the app reads in the store: what
they see and gain, not what the code did. You print one block ready to paste. A commit message is
the git-commit skill's job and a PR body the git-pr skill's; a changelog that lists every commit is
not store notes.

## 1. Commit range

`$ARGUMENTS` picks it:

- Empty or not a number: the current branch against the default branch, `origin/HEAD`, else
  `main`, else `master`. When none exists, ask the user for the base.
  `git log <base>..HEAD --pretty=format:"%h %s%n%b%n---"`
- A number N: the last N commits. `git log -n N --pretty=format:"%h %s%n%b%n---"`

Done when the log holds at least one commit. An empty range: say so and stop.

## 2. Keep what users see

Drop:

- `chore`, `refactor`, `test`, `docs`, `style`, `ci` and `build` commits;
- version bumps, release commits and dependency updates;
- internal infrastructure (schemas, tokens, build settings, entitlements), unless users see a
  change;
- a revert together with the commit it reverts.

Merge the commits about one feature into one change. Done when every change left is something a
user sees.

## 3. Write the bullets

3 to 6 bullets: with more than 6 changes, merge the smallest ones; with fewer than 3, write one
bullet per change. Each bullet is:

- in English, whatever language the conversation is in;
- one sentence under 120 characters, in sentence case, ending with a period;
- led by what the user sees or does, not by the commit type;
- with commas or hyphens (`-`), never em dashes (`—`) or en dashes (`–`);
- without marketing adjectives (revolutionary, stunning, amazing, powerful) and without internal
  names (CloudKit, JWT, schema, entitlement).

Three commits about an altitude chart, a fuel estimate and a weather snapshot become one bullet:

- Good: `- Ride details now show an altitude profile, weather at the start, and an estimated fuel use.`
- Bad: `- feat(rides): add altitude chart. feat(rides): add fuel estimate. feat(rides): add weather snapshot.`

Done when every change from step 2 is in a bullet.

## 4. Check and print

Rewrite every bullet that has `—` or `–`, a word that is not English (product names aside), or a
commit prefix such as `feat:`. Then print the bullets as one fenced code block, with nothing before
or after it:

````
```
- <change 1>.
- <change 2>.
- <change 3>.
```
````

Done when the block is the whole reply.
