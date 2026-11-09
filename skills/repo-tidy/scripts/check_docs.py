"""Lists doc files with names that are not lower-case kebab-case, and Markdown links that point nowhere.

Run from the repository root: python3 -I <skill>/scripts/check_docs.py
Exits 1 when a name or a link needs a look.
"""
import os
import re
import subprocess
import sys
from urllib.parse import unquote

# Names that GitHub, agents and build tools look for; they keep their case.
KEEP = {
    "AGENTS.md", "CLAUDE.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "SECURITY.md",
    "SUPPORT.md", "SKILL.md", "SUMMARY.md", "pull_request_template.md", "PULL_REQUEST_TEMPLATE.md",
    "CNAME", "CMakeLists.txt",
    "Cargo.toml", "Cargo.lock", "Dockerfile", "Makefile", "Gemfile", "Procfile",
}
MARKUP = (".md", ".rst", ".adoc")
# Lower-case ASCII words joined by hyphens, with extensions; a leading dot or underscore is a
# static-site generator's convention (.vitepress, _config.yml, _sidebar.md).
KEBAB = re.compile(r"[._]?[a-z0-9]+(-[a-z0-9]+)*(\.[a-z0-9]+)*")

CODE = re.compile(r"^(```|~~~).*?^\1[^\n]*$|`[^`\n]*`", re.MULTILINE | re.DOTALL)
TARGET = r"(<[^>]*>|[^)\s]+)"
INLINE = re.compile(r"\]\(\s*" + TARGET + r"(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)", re.MULTILINE)
SCHEME = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*:")

FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.MULTILINE | re.DOTALL)
HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$", re.MULTILINE)
EXPLICIT = re.compile(r"""<(?:[A-Za-z][^>]*?\sid|a\b[^>]*?\sname)\s*=\s*["']?([^"'\s>]+)""")
MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
HTML_TAG = re.compile(r"<[^>]+>")
CODE_SPAN = re.compile(r"(`[^`\n]*`)")
EMPHASIS = re.compile(r"\*|(?<!\w)_+|_+(?!\w)")


def is_kept(name: str) -> bool:
    return name in KEEP or name.startswith(("README", "LICENSE"))


def is_doc(parts: list[str]) -> bool:
    folders, name = parts[:-1], parts[-1]
    in_docs = any(folder.lower() == "docs" for folder in folders)
    return in_docs or name.endswith(MARKUP) or (name.endswith(".txt") and not folders)


def bad_names(paths: list[str]) -> list[str]:
    """Doc files, and everything in docs/, whose path is not lower-case kebab-case."""
    bad = []
    for path in paths:
        parts = path.split("/")
        if parts[0] == ".github" or not is_doc(parts):
            continue
        checked = parts[:-1] if is_kept(parts[-1]) else parts
        if not all(KEBAB.fullmatch(part) for part in checked):
            bad.append(path)
    return bad


def known_paths(paths: list[str]) -> set[str]:
    """Tracked files and their folders in exact case; the file system on macOS ignores case."""
    known = {"."}
    for path in paths:
        known.add(path)
        folder = os.path.dirname(path)
        while folder:
            known.add(folder)
            folder = os.path.dirname(folder)
    return known


def slug(heading: str) -> str:
    """GitHub's anchor for a heading; inline code keeps its text."""
    parts = CODE_SPAN.split(MD_LINK.sub(r"\1", heading))
    text = "".join(
        part.replace("`", "") if i % 2 else EMPHASIS.sub("", HTML_TAG.sub("", part))
        for i, part in enumerate(parts)
    )
    kept = "".join(c for c in text.lower() if c.isalnum() or c in " -_")
    return kept.replace(" ", "-")


def anchors_of(text: str) -> set[str]:
    """Lower-cased heading slugs and explicit ids of a Markdown file."""
    text = FENCE.sub("", text)
    anchors = {a.lower() for a in EXPLICIT.findall(text)}
    seen: dict[str, int] = {}
    for heading in HEADING.findall(text):
        base = slug(heading)
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def relative_links(text: str) -> list[str]:
    """Targets of Markdown links outside code, apart from URLs and other schemes."""
    prose = CODE.sub("", text)
    targets = [t.strip("<>") for t in INLINE.findall(prose) + DEFINITION.findall(prose)]
    return [t for t in targets if not SCHEME.match(t)]


def resolve(path: str, target: str) -> tuple[str, str]:
    """The repository path and the fragment that a link in the file at path points to."""
    file, _, fragment = target.partition("#")
    file = unquote(file)
    if not file:
        return path, fragment
    base = "" if file.startswith("/") else os.path.dirname(path)
    return os.path.normpath(os.path.join(base, file.lstrip("/"))), fragment


def broken_links(files: dict[str, str], exists) -> list[tuple[str, str]]:
    """Relative Markdown links whose file or #fragment does not exist, as (file, target)."""
    anchors = {path: anchors_of(text) for path, text in files.items()}
    broken = []
    for path, text in files.items():
        for target in relative_links(text):
            resolved, fragment = resolve(path, target)
            if target.partition("#")[0] and not exists(resolved):
                broken.append((path, target))
            elif fragment and resolved in anchors and unquote(fragment).lower() not in anchors[resolved]:
                broken.append((path, target))
    return broken


def main() -> int:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    paths = [p for p in listed if p and os.path.exists(p)]
    names = bad_names(paths)
    docs = {p: open(p, encoding="utf-8").read() for p in paths if p.endswith(".md")}
    links = broken_links(docs, known_paths(paths).__contains__)
    for path in names:
        print(f"name: {path}")
    for path, target in links:
        print(f"link: {path} -> {target}")
    print(f"{len(names)} names and {len(links)} links to look at")
    return 1 if names or links else 0


if __name__ == "__main__":
    sys.exit(main())
