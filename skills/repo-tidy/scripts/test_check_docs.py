import unittest

from check_docs import anchors_of, bad_names, broken_links, known_paths


class BadNames(unittest.TestCase):
    def test_flags_upper_case_and_underscores(self):
        self.assertEqual(
            bad_names(["docs/SPEC.md", "docs/smoke_test.md", "docs/spec.md", "src/app.ts"]),
            ["docs/SPEC.md", "docs/smoke_test.md"],
        )

    def test_flags_spaces_and_letters_outside_ascii(self):
        self.assertEqual(
            bad_names(["docs/Meeting Notes.md", "docs/þjónusta.md"]),
            ["docs/Meeting Notes.md", "docs/þjónusta.md"],
        )

    def test_keeps_names_that_tools_look_for(self):
        kept = ["README.md", "CLAUDE.md", "AGENTS.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md",
                "SUPPORT.md", "CODE_OF_CONDUCT.md", "CHANGELOG.md", "CMakeLists.txt",
                ".github/PULL_REQUEST_TEMPLATE.md", "sub/README.md", "skills/tidy/SKILL.md",
                "docs/book/src/SUMMARY.md", "docs/CNAME", "docs/_config.yml", "docs/_sidebar.md",
                "docs/.vitepress/config.md"]
        self.assertEqual(bad_names(kept), [])

    def test_keeps_the_pull_request_template_wherever_github_reads_it(self):
        kept = ["PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md",
                "skills/s/templates/github/pull_request_template.md"]
        self.assertEqual(bad_names(kept), [])

    def test_checks_directory_names_too(self):
        self.assertEqual(bad_names(["Docs/guide.md"]), ["Docs/guide.md"])

    def test_checks_markup_anywhere_and_text_at_the_root_and_in_docs(self):
        self.assertEqual(
            bad_names(["NOTES.txt", "docs/Diagram.svg", "docs/a_b.txt", "notes/Plan.rst"]),
            ["NOTES.txt", "docs/Diagram.svg", "docs/a_b.txt", "notes/Plan.rst"],
        )

    def test_leaves_code_and_fixtures_to_their_conventions(self):
        code = ["src/my_module.py", "src/App.swift", "migrations/0001_init.sql", "src/lib_rs/main.rs",
                "crates/doc/src/walk_tests/golden_A.txt"]
        self.assertEqual(bad_names(code), [])


class KnownPaths(unittest.TestCase):
    def test_holds_files_their_folders_and_the_root_in_exact_case(self):
        self.assertEqual(
            known_paths(["README.md", "docs/guides/run.md"]),
            {".", "README.md", "docs", "docs/guides", "docs/guides/run.md"},
        )


class BrokenLinks(unittest.TestCase):
    EXISTING = {".", "README.md", "docs", "docs/spec.md", "docs/guide.md", "docs/my file.md"}

    def broken(self, files):
        return broken_links(files, self.EXISTING.__contains__)

    def test_resolves_links_relative_to_the_file(self):
        files = {
            "README.md": "[Spec](docs/spec.md) [Gone](docs/old.md)",
            "docs/guide.md": "[Spec](spec.md#limits) [Up](../README.md) [Old case](SPEC.md)",
        }

        self.assertEqual(self.broken(files), [("README.md", "docs/old.md"), ("docs/guide.md", "SPEC.md")])

    def test_reads_titles_angle_brackets_encoded_and_root_paths(self):
        files = {"README.md": '[a](docs/gone.md "Title") [b](<docs/my file.md>) [c](docs/my%20file.md) '
                              "[d](/docs/spec.md) ![e](docs/img.png)"}

        self.assertEqual(self.broken(files), [("README.md", "docs/gone.md"), ("README.md", "docs/img.png")])

    def test_checks_reference_definitions(self):
        files = {"README.md": "See [spec][s].\n\n[s]: docs/spec.md\n[g]: <docs/gone.md> \"Gone\"\n"}

        self.assertEqual(self.broken(files), [("README.md", "docs/gone.md")])

    def test_skips_code(self):
        files = {"README.md": "```js\nhandlers[name](event)\n```\n~~~\n[x](y)\n~~~\nUse `foo[0](bar)` here."}

        self.assertEqual(self.broken(files), [])

    def test_skips_urls_and_other_schemes(self):
        files = {"README.md": "[a](https://x.is) [b](http://x.is) [c](mailto:a@x.is) [e](tel:+354)"}

        self.assertEqual(broken_links(files, lambda _: False), [])


class Anchors(unittest.TestCase):
    def test_slugs_follow_github(self):
        cases = {
            "Usage": "usage",
            "The `foo` option": "the-foo-option",
            "Hello, World!": "hello-world",
            "a  b": "a--b",
            "**Bold** and _it_": "bold-and-it",
            "See [the docs](http://x.is/a_b) now": "see-the-docs-now",
            "With <kbd>Ctrl</kbd> key": "with-ctrl-key",
            "snake_case name": "snake_case-name",
            "`__init__` method": "__init__-method",
            "Caf\u00e9 \u00fcn\u00ef 2": "caf\u00e9-\u00fcn\u00ef-2",
            "C# and C++": "c-and-c",
            "Title ##": "title",
            "dash - x": "dash---x",
        }
        for heading, slug in cases.items():
            with self.subTest(heading=heading):
                self.assertEqual(anchors_of(f"## {heading}\n"), {slug})

    def test_repeated_slugs_get_a_counter(self):
        self.assertEqual(anchors_of("# A\n## A\n### A\n"), {"a", "a-1", "a-2"})

    def test_ignores_fenced_indented_and_spaceless_headings(self):
        text = "```\n# in fence\n```\n~~~\n# in tilde fence\n~~~\n    # indented\n#nospace\n# Real\n"
        self.assertEqual(anchors_of(text), {"real"})

    def test_reads_explicit_ids_and_names(self):
        text = '<a id="x"></a> <a name=\'y\'></a> <div class="c" id=z>'
        self.assertEqual(anchors_of(text), {"x", "y", "z"})


class BrokenFragments(unittest.TestCase):
    def broken(self, files):
        return broken_links(files, lambda path: True)

    def test_checks_same_file_fragments(self):
        files = {"README.md": "# Usage\n[a](#usage) [b](#Usage) [c](#nope)"}

        self.assertEqual(self.broken(files), [("README.md", "#nope")])

    def test_checks_fragments_in_other_markdown_files(self):
        files = {
            "README.md": "[a](docs/guide.md#checks) [b](docs/guide.md#gone) [c](docs/guide.md#)",
            "docs/guide.md": "## Checks\n[up](../README.md#readme) [bad](../README.md#x)",
        }

        self.assertEqual(
            self.broken(files),
            [("README.md", "docs/guide.md#gone"), ("docs/guide.md", "../README.md#readme"),
             ("docs/guide.md", "../README.md#x")],
        )

    def test_reads_the_fragment_percent_decoded_and_lower_cased(self):
        files = {"README.md": "# Caf\u00e9 Menu\n[a](#caf%C3%A9-menu) [b](#CAF%c3%a9-MENU)\n<a id=\"Top\"></a> [c](#top)"}

        self.assertEqual(self.broken(files), [])

    def test_leaves_other_files_and_missing_markdown_alone(self):
        files = {"README.md": "[a](src/app.rs#L10) [b](img/logo.png#x) [c](docs/other.md#x) [d](https://x.is/#y)"}

        self.assertEqual(self.broken(files), [])


if __name__ == "__main__":
    unittest.main()
