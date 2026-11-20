#!/usr/bin/env python3
"""Pure-Python, no-ROS regression for D08 latest Owner compact evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "d08_latest_owner_evidence_once.py"
spec = importlib.util.spec_from_file_location("d08_latest_owner_evidence_once", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class LatestOwnerEvidenceTests(unittest.TestCase):
    def test_latest_pre_run_failure_not_previous_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / "once_20261119T120000Z_1" / "run_20261119T120001Z_aaaa"
            (old / "rmw_trace").mkdir(parents=True)
            (old / "rmw_trace" / "owner_first_gap_verdict.json").write_text('{"candidate":"OLD"}')
            new = root / "once_20261120T120000Z_2"
            new.mkdir()
            (new / "owner_console.log").write_text("D08_OWNER_RMW_TRACE_START_BLOCKED\n")
            output = root / "result.zip"
            mod.extract(root, output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn("session/owner_console.excerpt.txt", names)
                self.assertNotIn("run/rmw_trace/owner_first_gap_verdict.json", names)
                self.assertIn(b"TRACE_START_BLOCKED",
                              archive.read("session/owner_console.excerpt.txt"))

    def test_largest_sources_excluded_first_failure_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            session = root / "once_20261120T130000Z_3"
            run = session / "run_20261120T130001Z_zzzz"
            (run / "rmw_trace" / "ctf").mkdir(parents=True)
            (run / "assets").mkdir()
            cycle = run / "live_evidence" / "owner_replan_cycles" / "cycle_0000"
            cycle.mkdir(parents=True)
            (run / "rmw_trace" / "ctf" / "huge.bin").write_bytes(b"X" * (12 * 1024 * 1024))
            (run / "assets" / "model.onnx").write_bytes(b"X" * (12 * 1024 * 1024))
            (run / "rmw_trace" / "owner_first_gap_verdict.json").write_text(
                json.dumps({"candidate": "EVIDENCE_INCOMPLETE"}))
            (cycle / "verdict.json").write_text('{"first_boundary":"SCAN500"}')
            (session / "owner_console.log").write_text(
                "D08_OWNER_FIRST_BOUNDARY_RMW_CAUSE_UNDETERMINED\n"
                + ("healthy\n" * 30000)
                + "D08_OWNER_FIRST_SCAN_CAPTURE_INCOMPLETE_HOLD\n")
            output = root / "out.zip"
            mod.extract(root, output)
            self.assertLess(output.stat().st_size, 8 * 1024 * 1024)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn("run/rmw_trace/owner_first_gap_verdict.json", names)
                self.assertIn("cycles/cycle_0000/verdict.json", names)
                self.assertFalse(any("ctf" in n or ".onnx" in n or ".bin" in n for n in names))
                content = archive.read("session/owner_console.excerpt.txt")
                self.assertIn(b"CAUSE_UNDETERMINED", content)
                self.assertIn(b"CAPTURE_INCOMPLETE_HOLD", content)

    def test_absent_root_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                mod.extract(Path(folder) / "missing", Path(folder) / "out.zip")


    def test_gazebo_gui_segv_first_fault_witness_is_not_dropped(self):
        # Regression from WSL2 run_20261120T021303Z_tJM9UQ.
        # Old allowlist kept server/Nav2 logs but OMITTED the actual GUI log.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            session = root / "once_20261120T021259Z_795"
            live = session / "run_20261120T021303Z_tJM9UQ" / "live_evidence"
            live.mkdir(parents=True)
            (session / "owner_console.log").write_text(
                "D08_OWNER_GUI_REPLAN_LOOP_READY\n"
                "D08_REAL_GAZEBO_L2_BLOCKED RuntimeError:D08_OWNER_GUI_GAZEBO_CLIENT_EXITED\n")
            (live / "d08_owner_gazebo_gui.log").write_text(
                "[GUI] Loading plugin [gz-rendering-ogre2]\n"
                "Stack trace (most recent call last):\n"
                "Segmentation fault (Address not mapped to object)\n")
            (live / "verdict.json").write_text(json.dumps({
                "status": "BLOCKED",
                "blocker": "RuntimeError:D08_OWNER_GUI_GAZEBO_CLIENT_EXITED",
                "process_exit": {"d08_owner_gazebo_gui": -11, "gazebo_server": -11}
            }))
            output = root / "gui-fault.zip"
            mod.extract(root, output)
            with zipfile.ZipFile(output) as archive:
                gui = "logs/d08_owner_gazebo_gui.log.excerpt.txt"
                self.assertIn(gui, archive.namelist())
                self.assertIn(b"Segmentation fault", archive.read(gui))
                self.assertIn(b"REPLAN_LOOP_READY",
                              archive.read("session/owner_console.excerpt.txt"))
                self.assertIn(b'"d08_owner_gazebo_gui": -11',
                              archive.read("run/live_evidence/verdict.json"))

if __name__ == "__main__":
    unittest.main()
