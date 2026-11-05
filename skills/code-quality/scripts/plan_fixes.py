#!/usr/bin/env python3
"""Group selected findings into fix units with disjoint file sets, then into parallel waves."""
import argparse
import json

SEVERITIES = ["HIGH", "MEDIUM", "LOW"]
EFFORTS = ["S", "M", "L"]
RANK = {level: i for i, level in enumerate(SEVERITIES)}
UNIT_FINDING_CAP = 6


def touched_files(finding):
    files = {finding["file"]}
    files.update(r.split(":")[0] for r in finding.get("related", []))
    return files


def plan(findings, min_severity="LOW", ids=None, max_parallel=4):
    selected = [
        f for f in findings
        if (ids is None or f["id"] in ids) and RANK[f["severity"]] <= RANK[min_severity]
    ]

    parent = {f["id"]: f["id"] for f in selected}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner = {}
    for f in selected:
        for file in touched_files(f):
            if file in owner:
                parent[find(f["id"])] = find(owner[file])
            else:
                owner[file] = f["id"]

    groups = {}
    for f in selected:
        groups.setdefault(find(f["id"]), []).append(f)

    units = []
    for members in groups.values():
        units.append({
            "findings": [m["id"] for m in members],
            "files": sorted(set().union(*(touched_files(m) for m in members))),
            "severity": min((m["severity"] for m in members), key=RANK.__getitem__),
            "effort": max((m.get("effort", "S") for m in members), key=EFFORTS.index),
            "oversized": len(members) > UNIT_FINDING_CAP,
        })
    units.sort(key=lambda u: (RANK[u["severity"]], u["findings"][0]))
    for i, u in enumerate(units, start=1):
        u["unit"] = i

    numbers = [u["unit"] for u in units]
    waves = [numbers[i:i + max_parallel] for i in range(0, len(numbers), max_parallel)]
    return {
        "selected": len(selected),
        "units": units,
        "waves": waves,
        "oversized_units": [u["unit"] for u in units if u["oversized"]],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings", required=True, help="path to findings.json")
    parser.add_argument("--min-severity", choices=SEVERITIES, default="LOW")
    parser.add_argument("--ids", help="comma-separated finding IDs; overrides severity filter scope")
    parser.add_argument("--max-parallel", type=int, default=4)
    args = parser.parse_args()

    with open(args.findings) as f:
        findings = json.load(f)["findings"]
    ids = [i.strip() for i in args.ids.split(",")] if args.ids else None
    print(json.dumps(plan(findings, args.min_severity, ids, args.max_parallel), indent=2))


if __name__ == "__main__":
    main()
