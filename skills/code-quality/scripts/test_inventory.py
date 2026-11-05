import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import inventory

SCRIPTS_DIR = Path(__file__).resolve().parent

PY = "x = 1\n"


def paths(inv):
    return [f["path"] for f in inv["files"]]


class InventoryTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def make_repo(self, files):
        """Create a git repo with the given {relative_path: content} files, committed."""
        root = self.tmp_path / "repo"
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(git + ["-C", str(root), "add", "-A"], check=True)
        subprocess.run(git + ["-C", str(root), "commit", "-qm", "init"], check=True)
        return root


class Files(InventoryTestCase):
    def test_lists_only_git_tracked_source_files(self):
        root = self.make_repo({
            "src/a.py": PY,
            "README.md": "hi\n",
            "config.json": "{}\n",
            "assets/logo.svg": "<svg/>\n",
        })
        (root / "src" / "untracked.py").write_text(PY)
        inv = inventory.build(root)
        self.assertEqual(paths(inv), ["src/a.py"])

    def test_excludes_vendored_generated_and_minified(self):
        root = self.make_repo({
            "src/a.py": PY,
            "node_modules/x/index.js": "1\n",
            "vendor/lib.go": "package x\n",
            "dist/bundle.js": "1\n",
            "src/app.min.js": "1\n",
            "src/api_pb2.py": PY,
            "src/types.d.ts": "export {}\n",
            "migrations/0001_init.py": PY,
        })
        self.assertEqual(paths(inventory.build(root)), ["src/a.py"])

    def test_scope_limits_to_given_paths(self):
        root = self.make_repo({"src/a.py": PY, "lib/b.py": PY, "cli/c.py": PY})
        inv = inventory.build(root, scope=["src", "cli/c.py"])
        self.assertEqual(paths(inv), ["cli/c.py", "src/a.py"])

    def test_loc_counts_nonblank_lines(self):
        root = self.make_repo({"src/a.py": "a = 1\n\n\nb = 2\n   \n"})
        inv = inventory.build(root)
        self.assertEqual(inv["files"][0]["loc"], 2)
        self.assertEqual(inv["total_loc"], 2)

    def test_languages_counted_by_extension(self):
        root = self.make_repo({"src/a.py": PY, "src/b.py": PY, "web/c.ts": "let x = 1\n"})
        self.assertEqual(inventory.build(root)["languages"], {"py": 2, "ts": 1})


class Chunks(InventoryTestCase):
    def test_chunks_pack_directories_in_path_order_up_to_budget(self):
        six = "x\n" * 6
        root = self.make_repo({"a/f.py": six, "b/f.py": six, "c/f.py": six})
        inv = inventory.build(root, budget=13)
        self.assertEqual([c["files"] for c in inv["chunks"]], [["a/f.py", "b/f.py"], ["c/f.py"]])
        self.assertEqual([c["loc"] for c in inv["chunks"]], [12, 6])

    def test_directory_over_budget_is_split_by_file(self):
        six = "x\n" * 6
        root = self.make_repo({"a/1.py": six, "a/2.py": six, "a/3.py": six})
        inv = inventory.build(root, budget=10)
        self.assertEqual([c["files"] for c in inv["chunks"]], [["a/1.py"], ["a/2.py"], ["a/3.py"]])

    def test_chunk_count_capped_by_raising_budget(self):
        six = "x\n" * 6
        root = self.make_repo({f"d{i}/f.py": six for i in range(6)})
        inv = inventory.build(root, budget=6, max_chunks=2)
        self.assertEqual(len(inv["chunks"]), 2)
        self.assertIs(inv["oversized"], True)
        self.assertEqual(inv["budget"], 18)

    def test_agent_count_is_lenses_times_chunks(self):
        six = "x\n" * 6
        root = self.make_repo({"a/f.py": six, "b/f.py": six})
        inv = inventory.build(root, budget=6)
        self.assertEqual(inv["lenses"], ["DRY", "KISS", "YAGNI", "SOLID"])
        self.assertEqual(inv["agent_count"], 8)


class Cli(InventoryTestCase):
    def test_cli_prints_json(self):
        root = self.make_repo({"src/a.py": PY})
        out = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "inventory.py"), "--root", str(root), "--budget", "100"],
            capture_output=True, text=True, check=True,
        ).stdout
        data = json.loads(out)
        self.assertEqual(data["file_count"], 1)
        self.assertEqual(data["chunks"][0]["files"], ["src/a.py"])


if __name__ == "__main__":
    unittest.main()
