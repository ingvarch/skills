#!/usr/bin/env python3
"""Merge analyzer outputs (run/raw/*.json) into run/findings.json: validate, dedupe overlaps, assign stable IDs.
With --apply-verdicts, apply verifier verdicts (run/verdicts/*.json) to an existing findings.json."""
import argparse
import json
from pathlib import Path

PRINCIPLES = ["DRY", "KISS", "YAGNI", "SOLID"]
SEVERITIES = ["HIGH", "MEDIUM", "LOW"]
CONFIDENCES = ["HIGH", "MEDIUM", "LOW"]
EFFORTS = ["S", "M", "L"]
VERDICTS = ["CONFIRMED", "DOWNGRADED", "REJECTED"]
REQUIRED = {"principle", "severity", "confidence", "file", "line_start", "line_end", "title", "evidence", "why", "fix", "effort"}
RANK = {level: i for i, level in enumerate(SEVERITIES)}


def is_valid(f):
    return (
        isinstance(f, dict)
        and REQUIRED <= f.keys()
        and f["principle"] in PRINCIPLES
        and f["severity"] in SEVERITIES
        and f["confidence"] in CONFIDENCES
        and f["effort"] in EFFORTS
        and isinstance(f["line_start"], int)
        and isinstance(f["line_end"], int)
    )


def same_range(a, b):
    return a["file"] == b["file"] and a["line_start"] <= b["line_end"] and b["line_start"] <= a["line_end"]


def overlaps(a, b):
    return a["principle"] == b["principle"] and same_range(a, b)


def stronger(a, b):
    return a if RANK[a] <= RANK[b] else b


def absorb(target, other):
    target["severity"] = stronger(target["severity"], other["severity"])
    target["confidence"] = stronger(target["confidence"], other["confidence"])
    target["line_start"] = min(target["line_start"], other["line_start"])
    target["line_end"] = max(target["line_end"], other["line_end"])
    target["related"] += [r for r in other["related"] if r not in target["related"]]
    target["sources"] += [s for s in other["sources"] if s not in target["sources"]]


def sort_findings(findings):
    findings.sort(key=lambda f: (RANK[f["severity"]], f["file"], f["line_start"]))


def summarize(findings):
    return {
        "total": len(findings),
        "by_severity": {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITIES},
        "by_principle": {p: sum(1 for f in findings if f.get("principle") == p) for p in PRINCIPLES},
        "by_principle_severity": {
            p: {s: sum(1 for f in findings if f.get("principle") == p and f["severity"] == s) for s in SEVERITIES}
            for p in PRINCIPLES
        },
    }


def brief(finding):
    principle = finding["principle"] + (f"/{finding['rule']}" if finding.get("rule") else "")
    return f"{finding['id']} [{principle}] {finding['title']} ({finding['file']}:{finding['line_start']}-{finding['line_end']})"


def merge(raw_docs):
    valid, dropped = [], 0
    for doc in raw_docs:
        source = f"{doc.get('lens')}-{doc.get('chunk')}"
        for f in doc.get("findings", []):
            if not is_valid(f):
                dropped += 1
                continue
            item = dict(f)
            item["related"] = list(f.get("related", []))
            item["sources"] = [source]
            valid.append(item)

    merged, duplicates = [], 0
    for f in valid:
        target = next((m for m in merged if overlaps(m, f)), None)
        if target is None:
            merged.append(f)
        else:
            absorb(target, f)
            duplicates += 1

    sort_findings(merged)
    for i, f in enumerate(merged, start=1):
        f["id"] = f"QC-{i:03d}"
    for f in merged:
        f["overlaps_with"] = [o["id"] for o in merged if o is not f and same_range(o, f)]

    summary = summarize(merged)
    summary.update({"dropped_invalid": dropped, "merged_duplicates": duplicates})
    return {"summary": summary, "findings": merged}


def apply_verdicts(result, verdict_docs):
    verdict_by_id = {
        v["id"]: v
        for doc in verdict_docs
        for v in doc.get("verdicts", [])
        if isinstance(v, dict) and v.get("verdict") in VERDICTS
    }
    kept, rejected = [], []
    for f in result["findings"]:
        v = verdict_by_id.get(f["id"])
        if v is None:
            f["verified"] = "UNVERIFIED"
        elif v["verdict"] == "REJECTED":
            rejected.append({"id": f["id"], "reason": v.get("reason", "")})
            continue
        else:
            f["verified"] = v["verdict"]
            f["verdict_reason"] = v.get("reason", "")
            if v["verdict"] == "DOWNGRADED" and v.get("severity") in SEVERITIES:
                f["severity"] = v["severity"]
        kept.append(f)

    kept_ids = {f["id"] for f in kept}
    for f in kept:
        f["overlaps_with"] = [i for i in f.get("overlaps_with", []) if i in kept_ids]

    sort_findings(kept)
    summary = dict(result.get("summary", {}))
    summary.update(summarize(kept))
    summary.update({
        "confirmed": sum(1 for f in kept if f["verified"] == "CONFIRMED"),
        "downgraded": sum(1 for f in kept if f["verified"] == "DOWNGRADED"),
        "unverified": sum(1 for f in kept if f["verified"] == "UNVERIFIED"),
        "rejected": len(rejected),
    })
    return {"summary": summary, "findings": kept, "rejected": rejected}


def load_docs(run, subdir):
    docs, unreadable = [], []
    for path in sorted((run / subdir).glob("*.json")):
        try:
            docs.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            unreadable.append(str(path.relative_to(run)))
    return docs, unreadable


def print_summary(result, run):
    s = result["summary"]
    sev = ", ".join(f"{k} {v}" for k, v in s["by_severity"].items())
    print(f"Findings: {s['total']} ({sev})")
    print(f"{'':8}" + "".join(f"{level:>8}" for level in SEVERITIES))
    for p, counts in s["by_principle_severity"].items():
        print(f"{p:8}" + "".join(f"{counts[level]:>8}" for level in SEVERITIES))
    if "rejected" in s:
        print(f"Verdicts: confirmed {s['confirmed']}, downgraded {s['downgraded']}, rejected {s['rejected']}, unverified {s['unverified']}")
    else:
        print(f"Dropped invalid: {s['dropped_invalid']} | merged duplicates: {s['merged_duplicates']}")
    print(f"Unreadable files: {len(s['unreadable_files'])} | written: {run / 'findings.json'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="run directory containing raw/ (and verdicts/)")
    parser.add_argument("--apply-verdicts", action="store_true", help="apply verdicts/*.json to findings.json")
    parser.add_argument("--brief", metavar="SEVERITIES", help="print one line per finding at these severities (comma-separated) and exit")
    args = parser.parse_args()
    run = Path(args.run_dir)

    if args.brief:
        wanted = args.brief.split(",")
        result = json.loads((run / "findings.json").read_text())
        for f in result["findings"]:
            if f["severity"] in wanted:
                print(brief(f))
        return

    if args.apply_verdicts:
        docs, unreadable = load_docs(run, "verdicts")
        result = apply_verdicts(json.loads((run / "findings.json").read_text()), docs)
    else:
        docs, unreadable = load_docs(run, "raw")
        result = merge(docs)

    result["summary"]["unreadable_files"] = unreadable
    (run / "findings.json").write_text(json.dumps(result, indent=2))
    print_summary(result, run)


if __name__ == "__main__":
    main()
