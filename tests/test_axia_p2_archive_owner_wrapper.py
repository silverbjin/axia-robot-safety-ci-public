"""Wrapper pin and fail-closed contract; does NOT touch Owner archives."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/axia_p2_g05_g06_readonly_archive_once.sh"
TOOL = ROOT / "tools/axia_p2_archive_integrity_audit.py"


class ReadOnlyOneShotTest(unittest.TestCase):
    def test_script_parses_and_self_checks_without_network(self):
        syntax = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        selfcheck = subprocess.run(["bash", str(SCRIPT), "--self-check"], capture_output=True, text=True)
        self.assertEqual(selfcheck.returncode, 0, selfcheck.stderr)
        self.assertIn("NO_ROS NO_GOAL NO_FAULT NO_UPLOAD", selfcheck.stdout)

    def test_exact_public_source_and_byte_pinned_tool(self):
        text = SCRIPT.read_text()
        source = re.search(r"readonly PUBLIC_SOURCE_SHA='([0-9a-f]{40})'", text)
        blob = re.search(r"readonly PYTHON_BLOB_SHA='([0-9a-f]{40})'", text)
        self.assertIsNotNone(source)
        self.assertIsNotNone(blob)
        self.assertEqual(source.group(1), "300cb4688a97a75156699f63552cc7efb1c38e04")
        got = subprocess.check_output(["git", "hash-object", str(TOOL)], text=True).strip()
        self.assertEqual(got, blob.group(1))

    def test_no_owner_goal_fault_or_upload_command(self):
        text = SCRIPT.read_text()
        for forbidden in ("ros2 ", "gz sim", "colcon ", "SIGKILL", "kill -",
                          "gh issue", "gh api", "gh release", "YES-P2-", "curl -T",
                          "scp ", "rsync ", "upload-artifact"):
            self.assertNotIn(forbidden, text)
        self.assertIn("HISTORICAL_TAR_NOT_FOUND_NO_RERUN_REQUIRED", text)
        self.assertIn("AXIA_P2_ARCHIVE_ROOT", text)
        self.assertIn("p2-l3-owner-ulbEs3NU.tar.gz", text)


if __name__ == "__main__":
    unittest.main()
