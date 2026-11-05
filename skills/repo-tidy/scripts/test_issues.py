import unittest

from issues import is_transient, plan_actions, render_body

PLAN = {
    "repo": "owner/name",
    "milestones": [
        {"title": "M1: MVP", "description": "The MVP."},
        {"title": "M2: Monitoring", "description": "Next."},
    ],
    "issues": [
        {"key": "scaffold", "title": "Scaffold", "body": "Step 1.", "milestone": "M1: MVP", "done": "abc1234"},
        {"key": "dkim", "title": "Probe DKIM", "body": "Selector.", "milestone": "M1: MVP", "labels": ["enhancement"]},
        {"key": "own_domain", "title": "Own domain scores A", "body": "- [ ] DKIM ({issue:dkim})", "milestone": "M1: MVP"},
    ],
    "pull_requests": [{"number": 1, "milestone": "M1: MVP"}],
}
LABELS = {"enhancement", "chore"}


def actions(existing=None, milestones=None, plan=PLAN, labels=LABELS):
    return plan_actions(plan, existing or {}, milestones or {}, labels)


class RenderBody(unittest.TestCase):
    def test_replaces_issue_placeholders_with_numbers(self):
        self.assertEqual(render_body({"body": "See {issue:own_domain}."}, {"own_domain": 28}), "See #28.")

    def test_leaves_other_braces_alone(self):
        self.assertEqual(render_body({"body": "Uses `{pct}%`."}, {}), "Uses `{pct}%`.")

    def test_appends_where_done_work_happened(self):
        self.assertEqual(render_body({"body": "Step 4.", "done": "#1"}, {}), "Step 4.\n\nDone in #1.")

    def test_rejects_a_placeholder_for_an_unknown_issue(self):
        with self.assertRaises(KeyError):
            render_body({"body": "{issue:nope}"}, {})


class PlanActions(unittest.TestCase):
    def test_creates_everything_on_an_empty_repository(self):
        ops = [(a["op"], a.get("title") or a.get("number")) for a in actions()]

        self.assertEqual(ops, [
            ("milestone", "M1: MVP"),
            ("milestone", "M2: Monitoring"),
            ("issue", "Scaffold"),
            ("issue", "Probe DKIM"),
            ("issue", "Own domain scores A"),
            ("pr_milestone", 1),
        ])

    def test_skips_milestones_and_issues_that_exist(self):
        existing = {
            "Scaffold": {"number": 3, "state": "CLOSED", "milestone": "M1: MVP"},
            "Probe DKIM": {"number": 28, "state": "OPEN", "milestone": "M1: MVP"},
        }
        result = actions(existing, {"M1: MVP": "open"})

        self.assertEqual([a["op"] for a in result], ["milestone", "skip", "skip", "issue", "pr_milestone"])
        self.assertEqual(result[2], {"op": "skip", "key": "dkim", "title": "Probe DKIM", "number": 28,
                                     "milestone": "M1: MVP", "set_milestone": False, "close": False})

    def test_brings_an_existing_issue_into_its_milestone_and_closes_it_when_done(self):
        existing = {"Scaffold": {"number": 3, "state": "OPEN", "milestone": None}}
        skip = actions(existing)[2]

        self.assertEqual((skip["set_milestone"], skip["close"]), (True, True))

    def test_rejects_an_issue_in_an_unplanned_milestone(self):
        plan = {**PLAN, "issues": [{"key": "x", "title": "X", "body": "", "milestone": "M9"}]}

        with self.assertRaisesRegex(ValueError, "M9"):
            actions(plan=plan)

    def test_rejects_a_placeholder_that_points_forward(self):
        plan = {**PLAN, "issues": list(reversed(PLAN["issues"]))}

        with self.assertRaisesRegex(ValueError, "earlier"):
            actions(plan=plan)

    def test_rejects_a_duplicate_key(self):
        plan = {**PLAN, "issues": PLAN["issues"] + [{**PLAN["issues"][1], "title": "Other"}]}

        with self.assertRaisesRegex(ValueError, "dkim"):
            actions(plan=plan)

    def test_rejects_a_label_the_repository_lacks(self):
        with self.assertRaisesRegex(ValueError, "enhancement"):
            actions(labels={"chore"})

    def test_rejects_a_closed_milestone(self):
        with self.assertRaisesRegex(ValueError, "closed"):
            actions(milestones={"M1: MVP": "closed"})


class IsTransient(unittest.TestCase):
    def test_retries_server_and_network_failures(self):
        for message in ["GraphQL: Something went wrong while executing your query", "HTTP 502: Bad Gateway",
                        "dial tcp: i/o timeout", "read: connection reset by peer"]:
            self.assertTrue(is_transient(message), message)

    def test_stops_on_request_errors(self):
        for message in ["could not add label: 'chore' not found", "HTTP 422: Validation Failed"]:
            self.assertFalse(is_transient(message), message)


if __name__ == "__main__":
    unittest.main()
