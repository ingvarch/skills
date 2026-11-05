"""Creates GitHub milestones and issues from a JSON plan; see milestones.md for the plan format.

python3 -I <skill>/scripts/issues.py <scratchpad>/issues-plan.json [--dry-run]

Safe to rerun: milestones and issues whose titles exist are reused, so a run that stopped halfway
can simply be started again.
"""
import json
import re
import subprocess
import sys
import time

PLACEHOLDER = re.compile(r"\{issue:([^}]+)\}")
TRANSIENT = re.compile(r"something went wrong|HTTP 5\d\d|timeout|connection|EOF", re.IGNORECASE)


def render_body(issue: dict, numbers: dict[str, int]) -> str:
    body = PLACEHOLDER.sub(lambda m: f"#{numbers[m.group(1)]}", issue["body"])
    return f"{body}\n\nDone in {issue['done']}." if issue.get("done") else body


def is_transient(message: str) -> bool:
    return bool(TRANSIENT.search(message))


def plan_actions(plan: dict, existing: dict[str, dict], milestones: dict[str, str], labels: set[str]) -> list[dict]:
    """The steps a run takes, in order. Checks the whole plan before anything is created.

    `existing` maps issue titles to number, state and milestone; `milestones` maps titles to state.
    """
    planned = {m["title"] for m in plan["milestones"]}
    closed = sorted(t for t in planned if milestones.get(t) == "closed")
    if closed:
        raise ValueError(f"milestones {closed} are closed: reopen them or rename them in the plan")
    actions = [{"op": "milestone", **m} for m in plan["milestones"] if m["title"] not in milestones]
    seen: set[str] = set()
    for issue in plan["issues"]:
        title, key = issue["title"], issue["key"]
        if key in seen:
            raise ValueError(f"{title}: key {key!r} is used twice")
        if issue["milestone"] not in planned:
            raise ValueError(f"{title}: milestone {issue['milestone']!r} is not in the plan")
        unknown = sorted(set(issue.get("labels", [])) - labels)
        if unknown:
            raise ValueError(f"{title}: labels {unknown} do not exist; create them first")
        later = sorted(set(PLACEHOLDER.findall(issue["body"])) - seen)
        if later:
            raise ValueError(f"{title}: {later} must come earlier in the plan")
        seen.add(key)
        found = existing.get(title)
        if found:
            actions.append({
                "op": "skip", "key": key, "title": title, "number": found["number"],
                "milestone": issue["milestone"],
                "set_milestone": found["milestone"] != issue["milestone"],
                "close": bool(issue.get("done")) and found["state"] == "OPEN",
            })
        else:
            actions.append({"op": "issue", **issue})
    actions += [{"op": "pr_milestone", **pr} for pr in plan.get("pull_requests", [])]
    return actions


def gh(*args: str, attempts: int = 3) -> str:
    for attempt in range(1, attempts + 1):
        out = subprocess.run(["gh", *args], capture_output=True, text=True)
        if out.returncode == 0:
            return out.stdout.strip()
        if attempt == attempts or not is_transient(out.stderr):
            break
        time.sleep(5)
    raise RuntimeError(f"gh {' '.join(args[:2])}: {out.stderr.strip()}")


def existing_issues(repo: str) -> dict[str, dict]:
    rows = json.loads(gh("issue", "list", "--repo", repo, "--state", "all", "--limit", "1000",
                         "--json", "number,title,state,milestone"))
    return {r["title"]: {"number": r["number"], "state": r["state"],
                         "milestone": (r["milestone"] or {}).get("title")} for r in rows}


def create_issue(repo: str, action: dict, body: str) -> int:
    args = ["issue", "create", "--repo", repo, "--title", action["title"], "--body", body,
            "--milestone", action["milestone"]]
    for label in action.get("labels", []):
        args += ["--label", label]
    for _ in range(2):
        try:
            return int(gh(*args, attempts=1).rsplit("/", 1)[1])
        except RuntimeError as error:
            if not is_transient(str(error)):
                raise
            # GitHub sometimes fails after creating the issue; look before trying again.
            time.sleep(5)
            found = existing_issues(repo).get(action["title"])
            if found:
                return found["number"]
    return int(gh(*args, attempts=1).rsplit("/", 1)[1])


def run(plan: dict, dry_run: bool) -> None:
    repo = plan["repo"]
    milestones = dict(json.loads(gh("api", f"repos/{repo}/milestones?state=all&per_page=100",
                                    "--jq", "[.[] | [.title, .state]]")))
    labels = set(json.loads(gh("label", "list", "--repo", repo, "--limit", "1000", "--json", "name",
                               "--jq", "[.[].name]")))
    actions = plan_actions(plan, existing_issues(repo), milestones, labels)
    numbers: dict[str, int] = {}
    for action in actions:
        op = action["op"]
        if op == "skip":
            number = numbers[action["key"]] = action["number"]
            print(f"#{number} exists: {action['title']}")
            if action["set_milestone"]:
                print(f"  -> {action['milestone']}")
                if not dry_run:
                    gh("issue", "edit", str(number), "--repo", repo, "--milestone", action["milestone"])
            if action["close"]:
                print("  -> closed")
                if not dry_run:
                    gh("issue", "close", str(number), "--repo", repo, "--reason", "completed")
        elif op == "milestone":
            print(f"milestone: {action['title']}")
            if not dry_run:
                gh("api", f"repos/{repo}/milestones", "-f", f"title={action['title']}",
                   "-f", f"description={action['description']}")
        elif op == "issue":
            state = "closed" if action.get("done") else "open"
            if dry_run:
                numbers[action["key"]] = 0
                print(f"{state} [{action['milestone']}] {action['title']} {action.get('labels', [])}")
                continue
            number = numbers[action["key"]] = create_issue(repo, action, render_body(action, numbers))
            if action.get("done"):
                gh("issue", "close", str(number), "--repo", repo, "--reason", "completed")
            print(f"#{number} {state}: {action['title']}")
            time.sleep(1)
        elif op == "pr_milestone":
            print(f"PR #{action['number']} -> {action['milestone']}")
            if not dry_run:
                gh("pr", "edit", str(action["number"]), "--repo", repo, "--milestone", action["milestone"])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        run(json.load(f), "--dry-run" in sys.argv[2:])
