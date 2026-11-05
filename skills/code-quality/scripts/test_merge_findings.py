import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import merge_findings

SCRIPTS_DIR = Path(__file__).resolve().parent


def finding(**over):
    base = {
        "principle": "DRY",
        "severity": "MEDIUM",
        "confidence": "HIGH",
        "file": "src/a.py",
        "line_start": 10,
        "line_end": 20,
        "title": "duplicated validation",
        "evidence": "def validate(...)",
        "why": "same logic in two places",
        "fix": "extract helper",
        "effort": "S",
    }
    base.update(over)
    return base


def raw(lens, chunk, findings):
    return {"lens": lens, "chunk": chunk, "findings": findings}


class Merge(unittest.TestCase):
    def test_assigns_ids_sorted_by_severity_then_file_then_line(self):
        result = merge_findings.merge([
            raw("KISS", 1, [finding(principle="KISS", severity="LOW", file="src/z.py", line_start=1, line_end=2)]),
            raw("DRY", 1, [finding(severity="HIGH", file="src/b.py"), finding(severity="HIGH", file="src/a.py", line_start=50, line_end=60)]),
        ])
        ids = [(f["id"], f["severity"], f["file"]) for f in result["findings"]]
        self.assertEqual(ids, [
            ("QC-001", "HIGH", "src/a.py"),
            ("QC-002", "HIGH", "src/b.py"),
            ("QC-003", "LOW", "src/z.py"),
        ])

    def test_drops_invalid_findings_and_counts_them(self):
        bad = finding()
        del bad["file"]
        worse = finding(severity="BLOCKER")
        result = merge_findings.merge([raw("DRY", 1, [finding(), bad, worse])])
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["summary"]["dropped_invalid"], 2)

    def test_merges_overlapping_range_same_principle_keeping_max_severity(self):
        result = merge_findings.merge([
            raw("DRY", 1, [finding(severity="LOW", confidence="LOW", related=["src/b.py:1-5"])]),
            raw("DRY", 2, [finding(severity="HIGH", line_start=15, line_end=30, related=["src/c.py:1-5"])]),
        ])
        self.assertEqual(len(result["findings"]), 1)
        merged = result["findings"][0]
        self.assertEqual(merged["severity"], "HIGH")
        self.assertEqual(merged["confidence"], "HIGH")
        self.assertEqual(merged["line_start"], 10)
        self.assertEqual(merged["line_end"], 30)
        self.assertEqual(merged["related"], ["src/b.py:1-5", "src/c.py:1-5"])
        self.assertEqual(merged["sources"], ["DRY-1", "DRY-2"])
        self.assertEqual(result["summary"]["merged_duplicates"], 1)

    def test_does_not_merge_different_principles_or_disjoint_ranges(self):
        result = merge_findings.merge([
            raw("DRY", 1, [finding(), finding(line_start=40, line_end=50)]),
            raw("SOLID", 1, [finding(principle="SOLID", rule="SRP")]),
        ])
        self.assertEqual(len(result["findings"]), 3)

    def test_cross_principle_overlaps_are_cross_referenced(self):
        result = merge_findings.merge([
            raw("DRY", 1, [finding(severity="HIGH")]),
            raw("YAGNI", 1, [finding(principle="YAGNI", severity="LOW", line_start=15, line_end=18)]),
            raw("KISS", 1, [finding(principle="KISS", severity="MEDIUM", file="src/b.py")]),
        ])
        by_id = {f["id"]: f for f in result["findings"]}
        self.assertEqual(by_id["QC-001"]["overlaps_with"], ["QC-003"])
        self.assertEqual(by_id["QC-003"]["overlaps_with"], ["QC-001"])
        self.assertEqual(by_id["QC-002"]["overlaps_with"], [])

    def test_same_source_duplicates_recorded_once(self):
        result = merge_findings.merge([raw("DRY", 1, [finding(), finding(line_start=15, line_end=25)])])
        self.assertEqual(result["findings"][0]["sources"], ["DRY-1"])


class Summary(unittest.TestCase):
    def test_summary_counts_by_severity_and_principle(self):
        result = merge_findings.merge([
            raw("DRY", 1, [finding(severity="HIGH"), finding(severity="LOW", file="src/b.py")]),
            raw("YAGNI", 1, [finding(principle="YAGNI", severity="LOW", file="src/c.py")]),
        ])
        self.assertEqual(result["summary"]["by_severity"], {"HIGH": 1, "MEDIUM": 0, "LOW": 2})
        self.assertEqual(result["summary"]["by_principle"], {"DRY": 2, "KISS": 0, "YAGNI": 1, "SOLID": 0})
        self.assertEqual(result["summary"]["total"], 3)

    def test_summary_has_principle_by_severity_cross_tab(self):
        result = merge_findings.merge([
            raw("DRY", 1, [finding(severity="HIGH"), finding(severity="LOW", file="src/b.py")]),
            raw("YAGNI", 1, [finding(principle="YAGNI", severity="LOW", file="src/c.py")]),
        ])
        cross = result["summary"]["by_principle_severity"]
        self.assertEqual(cross["DRY"], {"HIGH": 1, "MEDIUM": 0, "LOW": 1})
        self.assertEqual(cross["KISS"], {"HIGH": 0, "MEDIUM": 0, "LOW": 0})


class MergeCli(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_cli_brief_lists_findings_at_given_severities(self):
        run = self.tmp_path / "run"
        (run / "raw").mkdir(parents=True)
        (run / "raw" / "DRY-1.json").write_text(json.dumps(raw("DRY", 1, [
            finding(severity="HIGH"),
            finding(principle="SOLID", rule="SRP", severity="MEDIUM", file="src/b.py", title="god class"),
            finding(severity="LOW", file="src/c.py", title="tiny"),
        ])))
        script = str(SCRIPTS_DIR / "merge_findings.py")
        subprocess.run([sys.executable, script, "--run-dir", str(run)], capture_output=True, check=True)
        out = subprocess.run(
            [sys.executable, script, "--run-dir", str(run), "--brief", "HIGH,MEDIUM"],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertEqual(out.splitlines(), [
            "QC-001 [DRY] duplicated validation (src/a.py:10-20)",
            "QC-002 [SOLID/SRP] god class (src/b.py:10-20)",
        ])

    def test_cli_reads_raw_dir_writes_findings_json(self):
        run = self.tmp_path / "run"
        (run / "raw").mkdir(parents=True)
        (run / "raw" / "DRY-1.json").write_text(json.dumps(raw("DRY", 1, [finding()])))
        (run / "raw" / "broken.json").write_text("{not json")
        out = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "merge_findings.py"), "--run-dir", str(run)],
            capture_output=True, text=True, check=True,
        )
        data = json.loads((run / "findings.json").read_text())
        self.assertEqual(data["findings"][0]["id"], "QC-001")
        self.assertEqual(data["summary"]["unreadable_files"], ["raw/broken.json"])
        self.assertIn("HIGH", out.stdout)


def merged(*findings):
    return {"summary": {}, "findings": list(findings)}


def f(id, severity, file="src/a.py", principle="DRY", overlaps_with=()):
    return {
        "id": id, "severity": severity, "file": file, "line_start": 1, "line_end": 2,
        "principle": principle, "overlaps_with": list(overlaps_with),
    }


def verdicts(*items):
    return {"batch": 1, "verdicts": list(items)}


class ApplyVerdicts(unittest.TestCase):
    def test_rejected_ids_are_pruned_from_overlaps_with(self):
        result = merge_findings.apply_verdicts(
            merged(f("QC-001", "HIGH", overlaps_with=["QC-002", "QC-003"]), f("QC-002", "LOW"), f("QC-003", "LOW")),
            [verdicts({"id": "QC-003", "verdict": "REJECTED", "reason": "no"})],
        )
        self.assertEqual(result["findings"][0]["overlaps_with"], ["QC-002"])

    def test_confirm_downgrade_reject(self):
        result = merge_findings.apply_verdicts(
            merged(f("QC-001", "HIGH"), f("QC-002", "HIGH", file="src/b.py"), f("QC-003", "MEDIUM", file="src/c.py")),
            [verdicts(
                {"id": "QC-001", "verdict": "CONFIRMED", "reason": "both copies read"},
                {"id": "QC-002", "verdict": "DOWNGRADED", "severity": "LOW", "reason": "two lines only"},
                {"id": "QC-003", "verdict": "REJECTED", "reason": "helper is used via decorator"},
            )],
        )
        by_id = {x["id"]: x for x in result["findings"]}
        self.assertEqual(by_id["QC-001"]["verified"], "CONFIRMED")
        self.assertEqual(by_id["QC-002"]["severity"], "LOW")
        self.assertEqual(by_id["QC-002"]["verified"], "DOWNGRADED")
        self.assertNotIn("QC-003", by_id)
        self.assertEqual(result["rejected"], [{"id": "QC-003", "reason": "helper is used via decorator"}])
        self.assertEqual(result["summary"]["rejected"], 1)
        self.assertEqual(result["summary"]["downgraded"], 1)

    def test_unverdicted_marked_unverified_ids_stable_order_by_severity(self):
        result = merge_findings.apply_verdicts(
            merged(f("QC-001", "HIGH"), f("QC-002", "MEDIUM", file="src/b.py"), f("QC-003", "LOW", file="src/c.py")),
            [verdicts({"id": "QC-001", "verdict": "DOWNGRADED", "severity": "LOW", "reason": "x"})],
        )
        self.assertEqual(
            [(x["id"], x["severity"], x["verified"]) for x in result["findings"]],
            [
                ("QC-002", "MEDIUM", "UNVERIFIED"),
                ("QC-001", "LOW", "DOWNGRADED"),
                ("QC-003", "LOW", "UNVERIFIED"),
            ],
        )
        self.assertEqual(result["summary"]["by_severity"], {"HIGH": 0, "MEDIUM": 1, "LOW": 2})
        self.assertEqual(result["summary"]["total"], 3)


class ApplyVerdictsCli(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_cli_apply_verdicts_rewrites_findings_json(self):
        run = self.tmp_path / "run"
        (run / "verdicts").mkdir(parents=True)
        (run / "findings.json").write_text(json.dumps(merged(f("QC-001", "HIGH"))))
        (run / "verdicts" / "1.json").write_text(json.dumps(verdicts({"id": "QC-001", "verdict": "REJECTED", "reason": "no"})))
        out = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "merge_findings.py"), "--run-dir", str(run), "--apply-verdicts"],
            capture_output=True, text=True, check=True,
        ).stdout
        data = json.loads((run / "findings.json").read_text())
        self.assertEqual(data["findings"], [])
        self.assertEqual(data["rejected"][0]["id"], "QC-001")
        self.assertIn("rejected 1", out)


if __name__ == "__main__":
    unittest.main()
