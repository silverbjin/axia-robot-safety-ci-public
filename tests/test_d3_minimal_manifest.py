import json
import re
import unittest
from pathlib import Path


class TestD3PublicManifest(unittest.TestCase):
    def test_exact_private_sha_and_strict_scope(self):
        path = Path(__file__).resolve().parents[1] / "ci/d3_minimal_manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "axia-d3-minimal-ci-v1")
        self.assertEqual(data["target_repo"], "silverbjin/axia-robot-safety-instructor")
        self.assertRegex(data["target_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(data["target_sha"], "5db2bfc1cdac944d78ed0f15349606e6f20184e3")
        self.assertEqual(data["scope"], "python-unit-static-only")
        for key in ("goals","faults","gazebo","physical_estop_certified"):
            self.assertIs(data[key], False)
        self.assertNotIn("token", path.read_text().lower())
        self.assertNotIn("solution", path.read_text().lower())


if __name__ == "__main__":
    unittest.main()
