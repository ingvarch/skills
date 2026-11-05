import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import plan_fixes

SCRIPTS_DIR = Path(__file__).resolve().parent


def finding(id, file, severity="MEDIUM", related=(), effort="S"):
    return {
        "id": id, "file": file, "severity": severity, "related": list(related),
        "effort": effort, "principle": "DRY", "title": id,
    }


def units(plan):
    return [sorted(u["findings"]) for u in plan["units"]]


class Plan(unittest.TestCase):
    def test_findings_touching_same_file_share_a_unit(self):
        plan = plan_fixes.plan([
            finding("QC-001", "src/a.py"),
            finding("QC-002", "src/a.py"),
            finding("QC-003", "src/b.py"),
        ])
        self.assertEqual(units(plan), [["QC-001", "QC-002"], ["QC-003"]])

    def test_related_files_join_units_transitively(self):
        plan = plan_fixes.plan([
            finding("QC-001", "src/a.py", related=["src/b.py:1-5"]),
            finding("QC-002", "src/b.py"),
            finding("QC-003", "src/c.py", related=["src/b.py:9-9"]),
            finding("QC-004", "src/d.py"),
        ])
        self.assertEqual(units(plan), [["QC-001", "QC-002", "QC-003"], ["QC-004"]])
        self.assertEqual(plan["units"][0]["files"], ["src/a.py", "src/b.py", "src/c.py"])

    def test_select_by_minimum_severity(self):
        plan = plan_fixes.plan([
            finding("QC-001", "src/a.py", severity="HIGH"),
            finding("QC-002", "src/b.py", severity="MEDIUM"),
            finding("QC-003", "src/c.py", severity="LOW"),
        ], min_severity="MEDIUM")
        self.assertEqual(units(plan), [["QC-001"], ["QC-002"]])

    def test_select_by_ids(self):
        plan = plan_fixes.plan([
            finding("QC-001", "src/a.py"),
            finding("QC-002", "src/b.py"),
        ], ids=["QC-002"])
        self.assertEqual(units(plan), [["QC-002"]])

    def test_waves_cap_parallelism_and_order_by_severity(self):
        plan = plan_fixes.plan([
            finding("QC-001", "src/a.py", severity="LOW"),
            finding("QC-002", "src/b.py", severity="HIGH"),
            finding("QC-003", "src/c.py", severity="MEDIUM"),
        ], max_parallel=2)
        self.assertEqual([[u for u in w] for w in plan["waves"]], [[1, 2], [3]])
        self.assertEqual([u["severity"] for u in plan["units"]], ["HIGH", "MEDIUM", "LOW"])

    def test_units_over_the_finding_cap_are_flagged_oversized(self):
        crowded = [finding(f"QC-{i:03d}", "src/a.py") for i in range(1, 8)]
        plan = plan_fixes.plan(crowded + [finding("QC-100", "src/z.py")])
        self.assertEqual(plan["oversized_units"], [1])
        self.assertIs(plan["units"][0]["oversized"], True)
        self.assertIs(plan["units"][1]["oversized"], False)


class PlanCli(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_cli_reads_findings_json_and_prints_plan(self):
        src = self.tmp_path / "findings.json"
        src.write_text(json.dumps({"findings": [finding("QC-001", "src/a.py")]}))
        out = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "plan_fixes.py"), "--findings", str(src), "--min-severity", "LOW"],
            capture_output=True, text=True, check=True,
        ).stdout
        plan = json.loads(out)
        self.assertEqual(plan["units"][0]["findings"], ["QC-001"])


if __name__ == "__main__":
    unittest.main()
