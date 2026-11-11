#!/usr/bin/env python3
"""Public synthetic D03 mirror regression. No instructor source or ROS runtime."""
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "d03_mirror_compare.sh"

class D03MirrorDiffContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.student = self.root / "student" / "block_A"
        self.mirror = self.root / "mirror" / "block_A"
        for root in (self.student, self.mirror):
            (root / "day03" / "scripts").mkdir(parents=True)
            (root / "day03" / "tests").mkdir(parents=True)
            (root / "day03" / "lesson.py").write_text("print('same')\n")

    def compare(self):
        return subprocess.run(
            ["bash", str(SCRIPT), str(self.student), str(self.mirror)],
            text=True, capture_output=True, check=False,
        )

    def test_generated_cache_does_not_block_identical_source(self):
        for rel in (
            "day03/__pycache__/lesson.cpython-312.pyc",
            "day03/scripts/__pycache__/helper.cpython-312.pyc",
            "day03/tests/__pycache__/test_safety.cpython-312.pyc",
            "day03/.pytest_cache/v/cache/nodeids",
        ):
            file = self.student / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("generated cache\n")
        outcome = self.compare()
        self.assertEqual(outcome.returncode, 0, outcome.stdout + outcome.stderr)

    def test_real_python_edit_still_blocks(self):
        (self.student / "day03" / "lesson.py").write_text("print('changed')\n")
        outcome = self.compare()
        self.assertEqual(outcome.returncode, 1, outcome.stdout + outcome.stderr)
        self.assertIn("lesson.py", outcome.stdout)

    def test_extra_noncache_file_still_blocks(self):
        (self.student / "day03" / "unexpected.py").write_text("x = 1\n")
        outcome = self.compare()
        self.assertEqual(outcome.returncode, 1, outcome.stdout + outcome.stderr)
        self.assertIn("unexpected.py", outcome.stdout)

if __name__ == "__main__":
    unittest.main()
