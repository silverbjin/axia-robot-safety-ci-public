"""Cycle36 public GUI-only regression: actual world + integrated display, no Goal."""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
SHARED=ROOT/"d06/scripts/g07_shared_gui_clients.sh"
SIDECAR=ROOT/"d06/scripts/d06_rviz_sidecar.sh"
RESTORE=ROOT/"d06/docs/G07_CYCLE36_RESTORE_POINT_AND_DEVELOPMENT_INVENTORY_20261116_KO.md"

class Cycle36PublicRestore(unittest.TestCase):
    def test_archive_precedes_gui_change(self):
        self.assertTrue(RESTORE.exists())
        s=RESTORE.read_text()
        for token in ("db1eec05e01e1db0d0d2e0c05610806ef4e499f9",
                      "420fd276ec1018f7fcc3f14873693cad02f080b4",
                      "30599879c12c7f3a1a12c14b8b39b656362fc5ed",
                      "Cycle36 (계획만)"):
            self.assertIn(token,s)
    def test_gui_only_restoration_uses_integrated_server_and_no_double_gz(self):
        s=SHARED.read_text()
        self.assertIn("AXIA_G07_CYCLE36_INTEGRATED_GUI",s)
        self.assertIn("G07_CYCLE36_INTEGRATED_GUI_NO_EXTERNAL_GZ",s)
        self.assertIn("G07_CYCLE36_WORLD_ENTITY",s)
        self.assertIn("gz service -l",s)
        self.assertIn("gz model",s)
    def test_owner_hardware_renderer_not_forced_to_llvmpipe(self):
        s=SHARED.read_text()
        self.assertIn('if [[ "$MODE" == ci ]]',s)
        self.assertIn('unset LIBGL_ALWAYS_SOFTWARE',s)
        self.assertIn('unset GALLIUM_DRIVER',s)
        self.assertIn("G07_CYCLE36_INTEGRATED_GUI_NO_EXTERNAL_GZ",s)
    def test_readonly_and_single_goal_ownership_preserved(self):
        s=SHARED.read_text()
        for bad in ("ros2 action send_goal","ros2 topic pub /cmd_vel",
                    "YES-P2-G07-GOAL","p2_owner_l3_wsl2.sh"):
            self.assertNotIn(bad,s)
        self.assertIn("g07_shared_gui_clients.sh",SIDECAR.read_text())
        p=subprocess.run(["bash","-n",str(SHARED)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__":
    unittest.main()
