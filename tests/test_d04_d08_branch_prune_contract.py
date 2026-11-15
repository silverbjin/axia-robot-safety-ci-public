"""No-network RED/GREEN safety tests for GitHub D04-D08 cleanup."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "scripts/axia_d04_d08_safe_prune.py"
spec = importlib.util.spec_from_file_location("prune", FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
REPO = "silverbjin/axia-robot-safety-ci-public"

class PruneTests(unittest.TestCase):
    def test_main_unrelated_p4_and_ops_not_scoped(self):
        self.assertFalse(m.scoped("main"))
        self.assertFalse(m.scoped("fix/p4-g07-other"))
        self.assertFalse(m.scoped("release/p2-owner"))
        self.assertTrue(m.scoped("docs/d04-main-consolidation-20261115"))
        self.assertTrue(m.scoped("release/d08-public-no-goal-ci-main-20261115"))

    def test_open_pr_both_head_and_base_protected(self):
        pulls = [
          {"head": {"ref": "feature/d08-open", "repo": {"full_name": REPO}},
           "base": {"ref": "fix/d08-source", "repo": {"full_name": REPO}}},
        ]
        self.assertTrue(m.open_pr_ref("feature/d08-open", pulls, REPO))
        self.assertTrue(m.open_pr_ref("fix/d08-source", pulls, REPO))
        self.assertFalse(m.open_pr_ref("fix/d08-source", pulls,
                                       "silverbjin/axia-robot-safety-student"))

    def test_inventory_deletes_only_main_ancestor_not_open_pr(self):
        def fake_api(path, method="GET"):
            if path == "repos/" + REPO:
                return {"default_branch": "main"}
            if path == f"repos/{REPO}/branches/main":
                return {"commit": {"sha": "abc"}}
            if "compare/main...docs/d04-merged" in path:
                return {"ahead_by": 0, "behind_by": 2}
            if "compare/main...fix/d08-unmerged" in path:
                return {"ahead_by": 3, "behind_by": 2}
            raise AssertionError("Unexpected API: " + path)
        branches = [
            {"name": "main", "commit": {"sha": "abc"}},
            {"name": "docs/d04-merged", "commit": {"sha": "b"}, "protected": False},
            {"name": "fix/d08-unmerged", "commit": {"sha": "c"}, "protected": False},
            {"name": "feat/d07-open", "commit": {"sha": "d"}, "protected": False},
            {"name": "feature/d05-protected", "commit": {"sha": "e"}, "protected": True},
            {"name": "feat/p4-unrelated", "commit": {"sha": "f"}, "protected": False},
        ]
        pulls = [{"head": {"ref": "feat/d07-open", "repo": {"full_name": REPO}},
                  "base": {"ref": "main", "repo": {"full_name": REPO}}}]
        with patch.object(m, "api", fake_api), patch.object(
            m, "listing", side_effect=lambda repo, kind: (
                pulls if "pulls" in kind else branches)):
            result = m.inventory(REPO)
        self.assertEqual([e["branch"] for e in result["eligible"]],
                         ["docs/d04-merged"])
        reasons = {r["branch"]: r["reason"] for r in result["preserved"]}
        self.assertEqual(reasons["fix/d08-unmerged"],
                         "UNMERGED_OR_CHERRY_PICKED")
        self.assertEqual(reasons["feat/d07-open"], "OPEN_PR_HEAD_OR_BASE")
        self.assertEqual(reasons["feature/d05-protected"], "BRANCH_PROTECTED")

if __name__ == "__main__":
    unittest.main()
