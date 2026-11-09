"""Lists agent files out of shape, docs that no AGENTS.md links to, and links in agent files that point nowhere.

Run from the repository root: python3 -I <skill>/scripts/check_agents.py
Exits 1 when something needs a look.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "repo-tidy", "scripts"))
from check_docs import CODE, MARKUP, broken_links, known_paths, relative_links, resolve  # noqa: E402

AGENT_FILES = {"AGENTS.md", "CLAUDE.md"}
IMPORTS = {"@AGENTS.md", "@./AGENTS.md"}
# A Claude Code import anywhere in prose; a word before the @ makes it an email address.
IMPORT = re.compile(r"(?<!\w)@(\S+)")
# Claude Code reads <folder>/.claude/CLAUDE.md as a second CLAUDE.md of <folder>.
CLAUDE_FOLDER = ".claude"
# Root files that are not docs an agent reads before a task.
NOT_PROJECT_DOCS = AGENT_FILES | {"CHANGELOG.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "SUPPORT.md"}


def prose_lines(text: str) -> list[str]:
    return [line.strip() for line in CODE.sub("", text).splitlines()]


def claude_imports(path: str, text: str, present: set[str]) -> list[str]:
    """@ tokens that name a personal file or a file in the repository, as Claude Code imports them."""
    tokens = (token.rstrip(".,;:!?)") for token in IMPORT.findall(CODE.sub("", text)))
    return [t for t in tokens if t.startswith("~/") or resolve(path, t)[0] in present]


def agent_files(paths: list[str], read, links: set[str]) -> list[str]:
    """Each folder with an agent file, and the root, needs AGENTS.md and a CLAUDE.md that imports it."""
    present = set(paths)
    folders = {""} | {os.path.dirname(p) for p in paths if os.path.basename(p) in AGENT_FILES}
    problems = []
    for folder in sorted(folders):
        if os.path.basename(folder) == CLAUDE_FOLDER:
            problems.append(f"{os.path.join(folder, 'CLAUDE.md')} holds rules outside AGENTS.md")
            continue
        agents, claude = os.path.join(folder, "AGENTS.md"), os.path.join(folder, "CLAUDE.md")
        symlinks = [f"{path} is a symlink" for path in (agents, claude) if path in links]
        if symlinks:
            problems += symlinks
            continue
        if agents not in present:
            problems.append(f"{agents} is missing")
        else:
            problems += [f"{agents} has the Claude Code import @{token}"
                         for token in claude_imports(agents, read(agents), present)]
        if claude not in present:
            problems.append(f"{claude} is missing")
        elif not IMPORTS & set(prose_lines(read(claude))):
            problems.append(f"{claude} does not import AGENTS.md")
    return problems


def is_project_doc(path: str) -> bool:
    parts = path.split("/")
    if parts[0] == ".github" or not path.endswith(MARKUP):
        return False
    if len(parts) == 1:
        return path not in NOT_PROJECT_DOCS and not path.startswith(("README", "LICENSE"))
    return any(folder.lower() == "docs" for folder in parts[:-1])


def unlinked_docs(paths: list[str], agents: dict[str, str]) -> list[str]:
    """Project docs that no AGENTS.md links to, directly or through a folder below a docs folder."""
    targets = {resolve(path, target)[0] for path, text in agents.items() for target in relative_links(text)}
    folders = {t for t in targets if any(part.lower() == "docs" for part in t.split("/")[:-1])}

    def linked(doc: str) -> bool:
        return doc in targets or any(doc.startswith(folder + "/") for folder in folders)

    return [p for p in paths if is_project_doc(p) and not linked(p)]


def agent_links(files: dict[str, str], exists) -> list[tuple[str, str]]:
    """Broken links in agent files; files holds every Markdown file, so fragments into docs are checked."""
    return [(path, target) for path, target in broken_links(files, exists)
            if os.path.basename(path) in AGENT_FILES]


def main() -> int:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    paths = [p for p in listed if p and os.path.exists(p)]
    texts = {p: open(p, encoding="utf-8").read() for p in paths if p.endswith(".md")}
    symlinks = {p for p in paths if os.path.islink(p)}
    files = agent_files(paths, texts.__getitem__, symlinks)
    agents = {p: text for p, text in texts.items() if os.path.basename(p) == "AGENTS.md"}
    docs = unlinked_docs(paths, agents)
    links = [(p, t) for p, t in agent_links(texts, known_paths(paths).__contains__) if p not in symlinks]
    for problem in files:
        print(f"agent: {problem}")
    for path in docs:
        print(f"doc: {path}")
    for path, target in links:
        print(f"link: {path} -> {target}")
    print(f"{len(files)} agent files, {len(docs)} docs and {len(links)} links to look at")
    return 1 if files or docs or links else 0


if __name__ == "__main__":
    sys.exit(main())
