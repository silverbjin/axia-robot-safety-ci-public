"""Real uploaded Owner G07 ZIP first visual boundary replay (NO ROS/NO GOAL).

Evidence: axia_g07_c37_gui_evidence_DaVV852A.zip SHA256
8c2d28baeaec823e76ff67ca3746f81145f681f38d1f6958f2f74c563d972c18,
23/23 inner SHA256 match, no XWD, X11 Qt Selection Owner only, Intel
Iris Xe D3D12 4.1. D07 Cycle19 confirmed real pixels with explicit
QT_QPA_PLATFORM=xcb and NVIDIA D3D12 GUI children; do not claim this
concludes one definite cause on G07 without an actual Owner screenshot.
"""
import importlib.util
import pathlib
import unittest

D06=pathlib.Path(__file__).resolve().parents[1]
SIDE=(D06/"scripts/g07_shared_gui_clients.sh")
HELPER=(D06/"live/g07_cycle38_gui_window_evidence.py")

SPEC=importlib.util.spec_from_file_location("gui_evidence",HELPER)
geo=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(geo)

# Sanitized verbatim snippets, no Owner private files.
OWNER_INTEL="""name of display: :0
0xc00004 "Qt Selection Owner for gz-sim-gui": () 3x3+0+0
0xa00004 "Qt Selection Owner for rviz2": () 3x3+0+0
0x200027 "Weston WM": () 10x10+0+0
"""
OWNER_GLX="""direct rendering: Yes
Vendor: Microsoft Corporation
Device: D3D12 (Intel(R) Iris(R) Xe Graphics)
Accelerated: yes
OpenGL version string: 4.1 (Compatibility Profile) Mesa 26.2.6
"""
D07_SUCCESS_X11='''0x500004 "Gazebo": () 1000x845+70+80
0x600004 "RViz": () 1450x900+70+80
0x700003 "Qt Selection Owner for rviz2": () 3x3+0+0'''
D07_SUCCESS_GPU="""Device: D3D12 (NVIDIA GeForce RTX 2060)
Accelerated: yes
OpenGL core profile version string: 4.2 (Core Profile) Mesa
"""

class FirstVisualBoundary(unittest.TestCase):
    def test_no_fake_x11_windows_from_owner_selection_objects(self):
        self.assertIsNone(geo.window_id(OWNER_INTEL,"gazebo"))
        self.assertIsNone(geo.window_id(OWNER_INTEL,"rviz"))
        self.assertFalse(geo.gpu_is_target_accelerated(OWNER_GLX,"NVIDIA"))
    def test_d07_proven_xcb_window_geometry_contract(self):
        self.assertEqual(geo.window_id(D07_SUCCESS_X11,"gazebo"),"0x500004")
        self.assertEqual(geo.window_id(D07_SUCCESS_X11,"rviz"),"0x600004")
        self.assertTrue(geo.gpu_is_target_accelerated(D07_SUCCESS_GPU,"NVIDIA"))
    def test_owner_gpu_and_xcb_only_gui_children_and_snapshots(self):
        s=SIDE.read_text(encoding="utf-8")
        self.assertIn('QT_QPA_PLATFORM=xcb',s)
        self.assertIn('QT_X11_NO_MITSHM=1',s)
        self.assertIn('MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA',s)
        self.assertIn('GALLIUM_DRIVER=d3d12',s)
        self.assertIn('G07_CYCLE38_OWNER_XWD_PIXELS_CAPTURED_CONTENT_NEEDS_REVIEW',s)
        self.assertIn('g07_cycle38_gui_window_evidence.py',s)
        self.assertIn('xwd -silent -id',s)
        # Never apply a GPU override to shared Gazebo backend/CM/Supervisor.
        self.assertIn('if [[ "$MODE" == ci ]]',s)
        self.assertNotIn('AXIA_G07_CYCLE38_CHANGES_GUARD_TTL',s)

if __name__=="__main__":
    unittest.main()
