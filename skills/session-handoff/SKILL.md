---
name: session-handoff
description: Write or update handoff.md so the next agent, starting with a fresh context, can continue this work - the goal, the progress, what worked, what did not, and the next steps. The file stays out of git. Use when the user wants to hand the work over, end the session, or continue in a clean context.
---

# session-handoff

Write the state of this work to `handoff.md`, so a new session can continue from that file alone.
You write the file; the user starts the next session with its path.

## 1. Read what exists

The root is `git rev-parse --show-toplevel`, or the working directory outside a git repository.
When `<root>/handoff.md` exists, read it first: the update keeps what still holds and drops what
this session made stale. An older `<root>/HANDOFF.md` counts too: read it. When git does not
track it (`git -C <root> ls-files --error-unmatch HANDOFF.md` fails), rename it. On a file system
that ignores case the two names are one file, and `mv -n` would skip it; elsewhere `-n` keeps a
newer `handoff.md`:

```bash
if [ <root>/HANDOFF.md -ef <root>/handoff.md ]; then mv <root>/HANDOFF.md <root>/handoff.md
else mv -n <root>/HANDOFF.md <root>/handoff.md; fi
```

When git tracks it, it belongs to the project: on a file system that ignores case, such as the
macOS default, it is the same file as `handoff.md`, so ask the user where to write before step 2.

Done when you know what the existing file says, or that there is none.

## 2. Write handoff.md

Five sections, facts only, with file paths, commands and error messages verbatim:

- `## Goal`: what the work is for and what done looks like.
- `## Progress`: what is done, the branch, and the changes that are not committed.
- `## What worked`: approaches that succeeded.
- `## What did not work`: approaches that failed and why, so the next agent does not repeat them.
- `## Next steps`: the actions to continue with, the first one first.

Done when a reader who has only this file knows the goal, the state and the next action.

## 3. Keep it out of git

In a git repository, when `git -C <root> check-ignore -q handoff.md` fails, append `/handoff.md` to
the file that `git -C <root> rev-parse --path-format=absolute --git-path info/exclude` prints. That
file is local and not tracked, so the working tree stays clean. Tell the user in one line.

Done when `git -C <root> check-ignore -q handoff.md` succeeds, or the root is not a git repository.

## 4. Hand over

Print the absolute path of `handoff.md`. The user starts the next session with it.

Done when the path is the last line of your reply.
