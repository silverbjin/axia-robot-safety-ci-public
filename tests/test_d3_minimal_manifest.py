import json, re, unittest
from pathlib import Path
class TestD3PublicManifest(unittest.TestCase):
    def test_exact_version_and_no_runtime_or_private_data(self):
        p=Path(__file__).resolve().parents[1]/"ci/d3_minimal_manifest.json"
        d=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(d["schema"],"axia-d3-minimal-ci-v2")
        self.assertEqual(d["target_repo"],"silverbjin/axia-robot-safety-instructor")
        self.assertEqual(d["target_sha"],"99c81a9f02efdf64d7a1e3ad40d45a00c7a6e37c")
        self.assertEqual(d["scope"],"python-unit-static-only")
        for name in ("goals","faults","gazebo","physical_estop_certified"):
            self.assertIs(d[name],False)
        self.assertIs(d["dynamic_scene"],True)
        self.assertEqual(len(d["source_blobs"]),9)
        for entry in d["source_blobs"]:
            self.assertRegex(entry["git_blob_sha"],r"^[0-9a-f]{40}$")
            self.assertNotIn("hidden_tests",entry["source"])
            self.assertNotIn("instructor/solutions",entry["source"])
        self.assertNotIn("token",p.read_text().lower())
if __name__=="__main__":unittest.main()
