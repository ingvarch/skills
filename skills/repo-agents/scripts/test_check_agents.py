import os
import subprocess
import sys
import tempfile
import unittest

from check_agents import agent_files, agent_links, unlinked_docs

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_agents.py")


class AgentFiles(unittest.TestCase):
    def check(self, files, links=()):
        return agent_files(list(files), files.__getitem__, set(links))

    def test_passes_agents_md_with_a_claude_md_that_imports_it(self):
        self.assertEqual(self.check({"AGENTS.md": "# AGENTS.md\n", "CLAUDE.md": "@AGENTS.md\n"}), [])

    def test_allows_claude_only_rules_beside_the_import(self):
        files = {"AGENTS.md": "", "CLAUDE.md": "@AGENTS.md\n\nDeploy with the /ship skill.\n"}

        self.assertEqual(self.check(files), [])

    def test_asks_for_both_files_at_the_root(self):
        self.assertEqual(self.check({"README.md": "# App"}), ["AGENTS.md is missing", "CLAUDE.md is missing"])

    def test_flags_a_claude_md_that_holds_the_rules_itself(self):
        self.assertEqual(
            self.check({"CLAUDE.md": "# Rules\nRun make test.\n"}),
            ["AGENTS.md is missing", "CLAUDE.md does not import AGENTS.md"],
        )

    def test_needs_the_import_on_its_own_line_outside_code(self):
        files = {"AGENTS.md": "", "CLAUDE.md": "  @AGENTS.md  \n", "api/AGENTS.md": "",
                 "api/CLAUDE.md": "See `@AGENTS.md` for the rules.\n", "web/AGENTS.md": "",
                 "web/CLAUDE.md": "```\n@AGENTS.md\n```\n", "cli/AGENTS.md": "", "cli/CLAUDE.md": "@./AGENTS.md\n"}

        self.assertEqual(
            self.check(files),
            ["api/CLAUDE.md does not import AGENTS.md", "web/CLAUDE.md does not import AGENTS.md"],
        )

    def test_flags_a_symlink_between_the_two_files(self):
        files = {"AGENTS.md": "# Rules\n", "CLAUDE.md": "# Rules\n", "api/AGENTS.md": "", "api/CLAUDE.md": ""}

        self.assertEqual(
            self.check(files, links={"CLAUDE.md", "api/AGENTS.md"}),
            ["CLAUDE.md is a symlink", "api/AGENTS.md is a symlink"],
        )

    def test_flags_imports_that_only_claude_code_follows(self):
        files = {
            "AGENTS.md": "@docs/style.md\n- Git workflow @docs/git.md\nSee @docs/api.md. Personal: @~/.claude/me.md\n",
            "CLAUDE.md": "@AGENTS.md", "docs/style.md": "", "docs/git.md": "", "docs/api.md": "",
        }

        self.assertEqual(self.check(files), [
            "AGENTS.md has the Claude Code import @docs/style.md",
            "AGENTS.md has the Claude Code import @docs/git.md",
            "AGENTS.md has the Claude Code import @docs/api.md",
            "AGENTS.md has the Claude Code import @~/.claude/me.md",
        ])

    def test_resolves_imports_from_the_agents_md_folder(self):
        files = {"AGENTS.md": "", "CLAUDE.md": "@AGENTS.md", "api/AGENTS.md": "Read @docs/schema.md first.",
                 "api/CLAUDE.md": "@AGENTS.md", "api/docs/schema.md": ""}

        self.assertEqual(self.check(files), ["api/AGENTS.md has the Claude Code import @docs/schema.md"])

    def test_leaves_mentions_emails_and_code_alone(self):
        files = {"AGENTS.md": "@ingvarch reviews.\nMail ops@docs/style.md or @team.\n`@docs/style.md`\n"
                              "```\n@docs/style.md\n```\n",
                 "CLAUDE.md": "@AGENTS.md", "docs/style.md": ""}

        self.assertEqual(self.check(files), [])

    def test_treats_a_claude_folder_as_the_claude_md_of_the_folder_above(self):
        files = {"AGENTS.md": "", "CLAUDE.md": "@AGENTS.md", ".claude/CLAUDE.md": "Run make test.",
                 "api/AGENTS.md": "", "api/CLAUDE.md": "@AGENTS.md", "api/.claude/CLAUDE.md": "Use pnpm."}

        self.assertEqual(self.check(files), [
            ".claude/CLAUDE.md holds rules outside AGENTS.md",
            "api/.claude/CLAUDE.md holds rules outside AGENTS.md",
        ])

    def test_checks_every_folder_with_an_agent_file(self):
        files = {"AGENTS.md": "", "CLAUDE.md": "@AGENTS.md", "web/CLAUDE.md": "Use pnpm.",
                 "api/AGENTS.md": ""}

        self.assertEqual(
            self.check(files),
            ["api/CLAUDE.md is missing", "web/AGENTS.md is missing", "web/CLAUDE.md does not import AGENTS.md"],
        )


class UnlinkedDocs(unittest.TestCase):
    def test_lists_docs_that_no_agents_md_links_to(self):
        paths = ["AGENTS.md", "docs/development.md", "docs/deployment.md"]
        agents = {"AGENTS.md": "- [docs/development.md](docs/development.md): read before a change."}

        self.assertEqual(unlinked_docs(paths, agents), ["docs/deployment.md"])

    def test_counts_docs_folders_at_any_depth_and_markup_at_the_root(self):
        paths = ["CONTRIBUTING.md", "ARCHITECTURE.md", "notes.rst", "docs/guide.adoc", "docs/README.md",
                 "packages/api/docs/schema.md"]

        self.assertEqual(unlinked_docs(paths, {}), paths)

    def test_leaves_out_files_that_are_not_project_docs(self):
        paths = ["README.md", "LICENSE.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "SUPPORT.md",
                 "AGENTS.md", "CLAUDE.md", "src/notes.md", "packages/api/README.md", "skills/s/SKILL.md",
                 ".github/docs/release.md", "docs/logo.png", "docs/openapi.yaml"]

        self.assertEqual(unlinked_docs(paths, {}), [])

    def test_accepts_fragments_reference_links_and_a_folder_of_one_kind(self):
        paths = ["docs/development.md", "docs/api.md", "docs/adr/0001-use-d1.md", "docs/adr/0002-drop-redis.md"]
        agents = {"AGENTS.md": "[a](docs/development.md#checks)\n- [ADRs](docs/adr/): read before a design change.\n\n"
                               "[api]: docs/api.md\n"}

        self.assertEqual(unlinked_docs(paths, agents), [])

    def test_resolves_links_relative_to_each_agents_md(self):
        paths = ["docs/style.md", "api/docs/schema.md"]
        agents = {"api/AGENTS.md": "[schema](docs/schema.md) [style](../docs/style.md)"}

        self.assertEqual(unlinked_docs(paths, agents), [])

    def test_needs_a_link_to_the_doc_itself(self):
        paths = ["docs/spec.md", "docs/deployment.md", "api/docs/schema.md"]
        agents = {
            "AGENTS.md": "All [docs](docs/), [api docs](api/docs) and [the api](api/). See `docs/spec.md`.\n"
                         "```\n[deploy](docs/deployment.md)\n```\n",
        }

        self.assertEqual(unlinked_docs(paths, agents), paths)


class AgentLinks(unittest.TestCase):
    def test_reports_broken_links_in_agent_files_only(self):
        files = {
            "AGENTS.md": "[a](docs/gone.md) [b](docs/dev.md#nope) [c](docs/dev.md#checks)",
            "CLAUDE.md": "@AGENTS.md\n[d](missing.md)",
            "docs/dev.md": "## Checks\n[e](gone.md)",
            "api/AGENTS.md": "[f](../docs/dev.md) [g](schema.md)",
        }

        self.assertEqual(
            agent_links(files, set(files).__contains__),
            [("AGENTS.md", "docs/gone.md"), ("AGENTS.md", "docs/dev.md#nope"), ("CLAUDE.md", "missing.md"),
             ("api/AGENTS.md", "schema.md")],
        )


class Main(unittest.TestCase):
    def run_in(self, files, links=()):
        with tempfile.TemporaryDirectory() as root:
            for path, text in files.items():
                os.makedirs(os.path.join(root, os.path.dirname(path)), exist_ok=True)
                with open(os.path.join(root, path), "w", encoding="utf-8") as f:
                    f.write(text)
            for link, target in links:
                os.symlink(target, os.path.join(root, link))
            env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
            subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
            return subprocess.run([sys.executable, "-I", SCRIPT], cwd=root, capture_output=True, text=True,
                                  env=env)

    def test_passes_a_repository_in_shape(self):
        result = self.run_in({"AGENTS.md": "- [docs/guide.md](docs/guide.md): read before a change.\n",
                              "CLAUDE.md": "@AGENTS.md\n", "docs/guide.md": "# Guide\n"})

        self.assertEqual((result.returncode, result.stdout),
                         (0, "0 agent files, 0 docs and 0 links to look at\n"))

    def test_reports_each_problem_and_fails(self):
        result = self.run_in({"AGENTS.md": "[gone](docs/gone.md)\n", "docs/guide.md": "# Guide\n"},
                             links=[("CLAUDE.md", "AGENTS.md")])

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.splitlines(), [
            "agent: CLAUDE.md is a symlink",
            "doc: docs/guide.md",
            "link: AGENTS.md -> docs/gone.md",
            "1 agent files, 1 docs and 1 links to look at",
        ])


if __name__ == "__main__":
    unittest.main()
