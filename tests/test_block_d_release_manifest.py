"""Block D stage-1 provenance contract. Metadata-only; no ROS/Gazebo/Goal."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "block_d/release/RELEASE_MANIFEST.json"
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class BlockDBaselineInventoryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_schema_and_stage(self):
        self.assertEqual(self.d["schema"], "axia.block_d.baseline_inventory.v1")
        self.assertEqual(self.d["stage"], "STAGE1_METADATA_ONLY")
        self.assertFalse(self.d["runtime_modified"])
        self.assertEqual(self.d["verification"], "METADATA_L0_NOT_ROS_OR_GAZEBO")

    def test_exact_demo_baseline_and_owner_boundary(self):
        demo = self.d["demo_baseline"]
        self.assertEqual(demo["id"], "AXIA-G07-T04-DEMO-BASELINE-20261120-jrCIgoGl")
        self.assertEqual(demo["student_runtime_sha"], "5c7983598fa3bcd7148433a06f37a4e78b091273")
        self.assertEqual(demo["owner_numeric_checks"], "21/21")
        self.assertTrue(demo["classroom_numeric_accepted"])
        for key in ("formal_safety_timing_accepted", "certified_estop",
                    "visual_content_verified", "original_raw_machine_l3_accepted"):
            self.assertIs(demo[key], False)
        self.assertEqual(demo["original_raw_machine_status"], "HOLD_RAW_REVIEW_AND_VISUAL_PENDING")
        for value in demo["owner_archive_sha256"].values():
            self.assertRegex(value, SHA256)

    def test_immutable_repository_pins_and_merge_scope(self):
        pins = self.d["repository_pins"]
        self.assertEqual(pins["student_main_before"]["sha"], "2ab0ac62c4cc359d398747dd065ff8b7f6692e00")
        self.assertEqual(pins["public_ci_main_before"]["sha"], "1f307691482b583b339218e43f9aacdb1ed06d9b")
        self.assertEqual(pins["instructor_main_before"]["sha"], "5f682eb2c26c6d649e80d78839dfa312625ddde4")
        self.assertEqual(pins["instructor_p3_staging"]["sha"], "fe92baf2c06834300a51c82de60b0ab2897b57d5")
        self.assertTrue(self.d["integration"]["demo_student_public_main_merged"])
        self.assertFalse(self.d["integration"]["p3_instructor_main_merged"])
        self.assertFalse(self.d["integration"]["block_d_curriculum_implemented"])
        self.assertEqual(self.d["integration"]["g07_stabilization"], "SEPARATE_HOLD")

    def test_exact_file_blob_sha1(self):
        expected = {
            "student_demo_doc": "4d255be8eca57ca9447474e62063d43892f9bfb8",
            "student_guard": "cfcc7d53d0e7d2fbd0450f80332f6ddc3e4c2f9f",
            "student_supervisor": "920f36c966c7b72a858e73e120bc36598948f5d2",
            "student_g07_runner": "8bf6c00209f106a5c68f2fc5c57542654932bce4",
            "public_demo_report": "58dd49845e57fe4a47ea2c1d8407e41cb734c654",
            "public_demo_derived": "ae7d594b5452d96cc8802bc53bc8ad578fe99fb7",
            "public_demo_script": "26570de6762db8ade5c92b9d821fad0ebe368374",
            "p3_oracle": "85dd0fa35b2e7982b0c86020fdd4f4952e6a039f",
            "p3_ros_bridge": "66ebe8e0120a0c5cdf76e3afff6257ec4d6df49f",
            "p3_risk_policy": "818a89077e95682c15906fba603b6eb8fe599d2c",
            "p3_g10_compound": "8ce0123e299e95fe5f49f2703ce55fa2250e220a",
            "p3_pnu_fixture": "4e86a997f840283d5fbddfa2b0e3da87cca343c1",
            "p3_g10_fixture": "620f769f812e32f2c3d1fa193629668090fa756f",
            "p3_g09_test": "3f79d3daaa80487579276fee752a04c91ae17cc4",
            "p3_g10_test": "34c2e34285926aeb65bd8c5b1ab74f0fef1d741d",
            "p3_ros_test": "bac0b95e10a22c3fbca6b002582d6bfe303517b3",
        }
        inventory = self.d["source_inventory"]
        self.assertEqual(len(inventory), len(expected))
        self.assertEqual({v["id"]: v["git_blob_sha1"] for v in inventory}, expected)
        self.assertEqual(len({(v["repository"], v["path"]) for v in inventory}), len(expected))
        for v in inventory:
            self.assertRegex(v["git_blob_sha1"], SHA1)
            self.assertRegex(v["ref_commit_sha"], SHA1)
            self.assertTrue(v["path"])
            self.assertIn(v["visibility"], ("public", "private"))
            if v["visibility"] == "private":
                self.assertEqual(v["repository"], "silverbjin/axia-robot-safety-instructor")

    def test_existing_public_ci_evidence_is_scoped(self):
        expected = {44653465671: "L2", 44478344652: "L2",
                    43383912097: "L0", 43387460089: "L1",
                    43388169083: "L0", 43455456960: "L2"}
        runs = self.d["prior_public_ci"]
        self.assertEqual({v["run_id"]: v["level"] for v in runs}, expected)
        for v in runs:
            self.assertEqual(v["conclusion"], "success")
            self.assertRegex(v["workflow_head_sha"], SHA1)
            self.assertTrue(v["scope"])
            self.assertEqual(v["repository"], "silverbjin/axia-robot-safety-ci-public")

    def test_safety_scope_and_no_overclaim(self):
        scope = self.d["safety_boundaries"]
        self.assertEqual(scope["scan_ttl_ms"], 300)
        self.assertEqual(scope["cm_guard_ttl_ms"], 150)
        self.assertTrue(scope["unchanged"])
        self.assertIs(self.d["demo_baseline"]["certified_estop"], False)
        self.assertEqual(scope["g09_person_input"], "SYNTHETIC_NOT_REAL_CAMERA")
        self.assertEqual(scope["stop_kind"], "SIMULATION_SOFTWARE_STOP_NOT_CERTIFIED_ESTOP")
        self.assertEqual(scope["g11_formal"], "NOT_ACCEPTED")

    def test_no_private_source_or_raw_evidence_in_public_manifest(self):
        txt = MANIFEST.read_text(encoding="utf-8")
        for forbidden in ("owner-moving-jrCIgoGl.tar.gz\\n", "PRIVATE KEY",
                          "BEGIN RSA PRIVATE", "BEGIN OPENSSH PRIVATE"):
            self.assertNotIn(forbidden, txt)
        self.assertEqual(self.d["privacy"]["private_source_content_included"], False)
        self.assertEqual(self.d["privacy"]["owner_raw_included"], False)


if __name__ == "__main__":
    unittest.main()
