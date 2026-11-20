#!/usr/bin/env python3
"""D08 Owner WSLg real SIGSEGV contract: only Gazebo GUI switches to software GL."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "d08/scripts/d08_public_gazebo_l2.py"

def calls_by_label(tree):
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_start":
            if node.args and isinstance(node.args[0], ast.Constant):
                found[node.args[0].value] = node
    return found

class OwnerWslgRendererIsolation(unittest.TestCase):
    def test_field_gui_segv_route_requires_isolated_software_gl(self):
        # Sanitized evidence: observed stack, not a simulated Gazebo runtime PASS.
        stack = ("libqxcb-glx-integration.so glXChooseFBConfig "
                 "libgallium-26.2.6 libd3d12core.so libnvwgf2umx.so "
                 "Segmentation fault [0xa100]")
        self.assertIn("libnvwgf2umx.so", stack)
        self.assertIn("glXChooseFBConfig", stack)
        src = RUNTIME.read_text(encoding="utf-8")
        tree = ast.parse(src)
        calls = calls_by_label(tree)
        gui = calls["d08_owner_gazebo_gui"]
        self.assertEqual(gui.args[2].id, "owner_gui_env",
                         "Gazebo GUI must use private env; shared env routes through WSL D3D12")
        self.assertIn("owner_gui_env=dict(env)", src)
        self.assertIn("owner_gui_env['LIBGL_ALWAYS_SOFTWARE']='1'", src)
        self.assertIn("owner_gui_env.pop('GALLIUM_DRIVER',None)", src)
        self.assertIn("owner_gui_env.pop('MESA_D3D12_DEFAULT_ADAPTER_NAME',None)", src)

    def test_server_nav2_and_other_processes_keep_original_gpu_and_ttl(self):
        src = RUNTIME.read_text(encoding="utf-8")
        calls = calls_by_label(ast.parse(src))
        for label in ("gazebo_server", "d08_official_nav2_one_world",
                      "rgbd_bridge", "d08_ci_gazebo_gui"):
            with self.subTest(process=label):
                self.assertEqual(calls[label].args[2].id, "env")
        self.assertIn("D08_OWNER_GUI_GAZEBO_CLIENT_EXITED", src)
        self.assertIn("result['status']='BLOCKED'", src)
        self.assertNotIn("env['LIBGL_ALWAYS_SOFTWARE']='1'\n            owner_gz_gui", src)

if __name__ == "__main__":
    unittest.main()
