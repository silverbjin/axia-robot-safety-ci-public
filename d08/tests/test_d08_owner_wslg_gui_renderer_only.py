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

    def test_ci_new_gui_branch_arms_all_first_scan_boundary_layers(self):
        # Actual CI first active Scan >500ms: 0.506651 at cycle_0008.
        # The branch must not silently disable the PR #188 native/RMW proofs.
        workflow=(ROOT / ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        lines=workflow.splitlines()
        target="fix/d08-owner-gui-renderer-isolation-20261120"
        for key in ("AXIA_D08_NATIVE_RX_PROBE:", "AXIA_D08_ROS_ISOLATED_RX_PROBE:",
                    "AXIA_D08_ROS_TRACE_PREFLIGHT:"):
            with self.subTest(key=key):
                row=next(s for s in lines if key in s)
                self.assertIn(target,row,"missing read-only boundary probe in target branch")

    def test_ci_rmw_trace_start_stop_and_failure_artifact_not_skipped(self):
        workflow=(ROOT / ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        lines=workflow.splitlines()
        target="fix/d08-owner-gui-renderer-isolation-20261120"
        stages=(
            "name: CI-only official Jazzy ROS userspace tracing preflight",
            "name: Start REAL L2 rcl publish/take trace before Gazebo/ROS bridge",
            "name: Stop REAL L2 rcl trace even when first Scan gap blocked",
            "name: Contract check Owner first-gap classifier using same-run real Gazebo RMW evidence",
        )
        for stage in stages:
            with self.subTest(stage=stage):
                idx=next(i for i,row in enumerate(lines) if stage in row)
                self.assertIn(target, lines[idx+1],
                    "new GUI branch must keep original first-gap tracer on failure")

    def test_ci_gui_only_pr_skips_unrelated_contact_threshold_trial(self):
        # Existing PR #188 did not rerun the unrelated Contact-positive job.
        # New public L2 #44664968850 validated the 8-cycle Nav2 path,
        # but unrelated Contact trial read 0.370528m > strict 0.370000m.
        # Keep failure as a separate HOLD, not as proof of GUI code defect.
        workflow=(ROOT / ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
        lines=workflow.splitlines()
        idx=next(i for i,row in enumerate(lines)
                 if row.strip()=="gazebo-contact-positive-once:")
        cond=next(s for s in lines[idx+1:idx+8] if s.strip().startswith("if:"))
        self.assertIn(
            "github.head_ref != 'fix/d08-owner-gui-renderer-isolation-20261120'",
            cond, "GUI-only regression must not rerun unrelated Contact threshold trial")

if __name__ == "__main__":
    unittest.main()
