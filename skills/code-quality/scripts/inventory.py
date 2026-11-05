#!/usr/bin/env python3
"""Inventory git-tracked source files and pack them into review chunks for analyzer agents."""
import argparse
import json
import math
import subprocess
from pathlib import Path

LENSES = ["DRY", "KISS", "YAGNI", "SOLID"]
SOURCE_EXT = {
    "py", "js", "jsx", "mjs", "cjs", "ts", "tsx", "go", "rs", "java", "kt", "kts", "swift",
    "rb", "php", "cs", "c", "h", "cc", "cpp", "hpp", "m", "mm", "scala", "ex", "exs", "dart",
    "lua", "sh", "fish", "vue", "svelte",
}
EXCLUDED_DIRS = {
    "node_modules", "vendor", "dist", "build", "out", "target", "coverage", "__pycache__",
    ".venv", "venv", ".next", ".nuxt", "generated", "migrations", ".git",
}
EXCLUDED_SUFFIXES = (
    ".min.js", ".min.css", ".d.ts", "_pb2.py", "_pb2_grpc.py", ".pb.go", ".generated.ts", ".generated.js",
)


def tracked_files(root):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def is_source(rel):
    parts = Path(rel).parts
    if any(p in EXCLUDED_DIRS for p in parts[:-1]):
        return False
    if rel.endswith(EXCLUDED_SUFFIXES):
        return False
    return Path(rel).suffix.lstrip(".").lower() in SOURCE_EXT


def in_scope(rel, scope):
    if not scope:
        return True
    return any(rel == s.rstrip("/") or rel.startswith(s.rstrip("/") + "/") for s in scope)


def count_loc(path):
    with open(path, errors="replace") as f:
        return sum(1 for line in f if line.strip())


def pack(files, budget):
    """Pack files (sorted by path) into chunks: whole directories first, files one by one when a directory exceeds budget."""
    groups = {}
    for f in files:
        groups.setdefault(str(Path(f["path"]).parent), []).append(f)
    chunks, current, current_loc = [], [], 0

    def flush():
        nonlocal current, current_loc
        if current:
            chunks.append(current)
        current, current_loc = [], 0

    def add(items, loc):
        nonlocal current, current_loc
        if current and current_loc + loc > budget:
            flush()
        current.extend(items)
        current_loc += loc

    for group in groups.values():
        group_loc = sum(f["loc"] for f in group)
        if group_loc <= budget:
            add(group, group_loc)
        else:
            flush()
            for f in group:
                add([f], f["loc"])
    flush()
    return [{"id": i + 1, "loc": sum(f["loc"] for f in c), "files": [f["path"] for f in c]} for i, c in enumerate(chunks)]


def build(root, scope=None, budget=5000, max_chunks=4):
    root = Path(root)
    scope = scope or []
    files = [
        {"path": rel, "loc": count_loc(root / rel)}
        for rel in sorted(tracked_files(root))
        if is_source(rel) and in_scope(rel, scope)
    ]
    total = sum(f["loc"] for f in files)
    languages = {}
    for f in files:
        ext = Path(f["path"]).suffix.lstrip(".").lower()
        languages[ext] = languages.get(ext, 0) + 1

    chunks = pack(files, budget)
    oversized = len(chunks) > max_chunks
    if oversized:
        budget = math.ceil(total / max_chunks)
        chunks = pack(files, budget)
        while len(chunks) > max_chunks:
            budget = math.ceil(budget * 1.2)
            chunks = pack(files, budget)

    return {
        "root": str(root),
        "scope": scope,
        "file_count": len(files),
        "total_loc": total,
        "languages": languages,
        "budget": budget,
        "max_chunks": max_chunks,
        "oversized": oversized,
        "lenses": LENSES,
        "chunks": chunks,
        "agent_count": len(LENSES) * len(chunks),
        "files": files,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--scope", nargs="*", default=[], help="paths relative to root; empty = whole repo")
    parser.add_argument("--budget", type=int, default=5000, help="max non-blank LOC per chunk")
    parser.add_argument("--max-chunks", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.scope, args.budget, args.max_chunks), indent=2))


if __name__ == "__main__":
    main()
