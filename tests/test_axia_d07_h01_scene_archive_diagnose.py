"""L0 synthetic archive regression; scene source/transport != WSLg pixel proof."""
from io import BytesIO
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from axia_d07_h01_scene_archive_diagnose import diagnose

WORLD = ('<sdf version="1.6" xmlns:xacro="http://www.ros.org/wiki/xacro">'
         '<xacro:arg name="headless" default="true"/>'
         '<world name="default">'
         '<plugin filename="gz-sim-scene-broadcaster-system" '
         'name="gz::sim::systems::SceneBroadcaster"/>'
         '</world></sdf>')
MANIFEST = json.dumps({
    "scene_broadcaster_count": 1,
    "scope": "D07_H01_GUI_READONLY_SIM_ONLY",
    "overlay_sha256": hashlib.sha256(WORLD.encode()).hexdigest(),
})
TOPICS = "/world/default/clock\n/world/default/stats\n/world/default/scene/info\n/world/default/pose/info\n"


def make_archive(root: Path, real_scene=True) -> Path:
    path = root / "owner-test.tar.gz"
    entries = {
        "real-l2/d07_gui_scene_world.sdf.xacro": WORLD,
        "real-l2/d07_gui_scene_world_manifest.json": MANIFEST,
        "real-l2/d07_gui_transport_topics.txt": TOPICS if real_scene else
                                            "/world/default/clock\n/world/default/stats\n",
        "real-l2/d07_gui_watcher.log": "D07_H01_GUI_CHILDREN_SPAWNED\n",
        "gui_diagnostics/gazebo_scene.xwd": "X" * 512,
        "gui_diagnostics/rviz_scene.xwd": "X" * 512,
    }
    with tarfile.open(path, "w:gz") as tf:
        for key, value in entries.items():
            raw = value.encode()
            info = tarfile.TarInfo("d07-h01-owner-test/" + key)
            info.size = len(raw)
            tf.addfile(info, BytesIO(raw))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    Path(str(path) + ".sha256").write_text(digest + "  " + path.name + "\n")
    return path


class SceneArchiveReadOnlyTest(unittest.TestCase):
    def test_synthetic_scene_and_topics_candidate_never_pixel_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            info = diagnose(make_archive(Path(t)))
        self.assertEqual(info["status"],
                         "D07_H01_SCENE_SOURCE_AND_TRANSPORT_VERIFIED")
        self.assertTrue(info["sha256_sidecar_verified"])
        self.assertTrue(info["scene_source_unconditional"])
        self.assertTrue(info["scene_runtime_topics_observed"])
        self.assertEqual(info["render_xwd_count"], 2)
        self.assertFalse(info["gazebo_3d_scene_render_proven"])
        self.assertFalse(info["owner_wsl2_gui_l3_accepted"])
        self.assertFalse(info["goal_sent"])

    def test_missing_real_scene_publishers_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            info = diagnose(make_archive(Path(t), real_scene=False))
        self.assertEqual(info["reason"],
                         "SCENE_BROADCASTER_RUNTIME_TOPICS_MISSING")
        self.assertEqual(info["status"], "D07_H01_SCENE_DIAG_HOLD")

    def test_checksum_tampering_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            path = make_archive(Path(t))
            Path(str(path) + ".sha256").write_text("0" * 64 + "  broken\n")
            info = diagnose(path)
        self.assertEqual(info["reason"],
                         "SHA256_SIDECAR_MISSING_OR_MISMATCH")
        self.assertFalse(info["sha256_sidecar_verified"])


if __name__ == "__main__":
    unittest.main()
