"""Cycle23 RED: Owner WSL2 and CI Marker observer was pinned onto CM CPU.

4CPU CI old layout: CM{1,2}, Marker{2}, Goal{2,3}.
8CPU WSL2 new candidate layout: CM{1,6}, Marker{6}, Goal{2,3,4,5}.
This is a plausible CPU contention contributor, NOT proven CM first-gap cause.
Only public GUI/Marker CPU selection changes; private official CM mask remains
exactly the Cycle22 SHA 124edc82...; Guard 150ms remains unchanged.
"""
import unittest
from pathlib import Path
from d06.live.d06_gui_cpu_plan import select_cpu,select_monitor_cpu

class Cycle23CompleteCpuRole(unittest.TestCase):
    def test_ci_four_cpu_marker_avoids_both_cm_cores(self):
        cpus=[0,1,2,3]
        cm={1,2}
        self.assertEqual(select_cpu(cpus),0)
        self.assertEqual(select_monitor_cpu(cpus),3)
        self.assertFalse({select_monitor_cpu(cpus)}&cm)

    def test_owner_eight_cpu_marker_avoids_new_exclusive_cm_mask(self):
        cpus=list(range(8))
        cm={1,6}
        self.assertEqual(select_monitor_cpu(cpus),2)
        self.assertFalse({select_monitor_cpu(cpus)}&cm)
        self.assertIn(select_monitor_cpu(cpus),{2,3,4,5})

    def test_other_cpu_topologies_and_nonzero_cpuset_offsets(self):
        for cpus,cm,want in (
            ([0,1,2,3,4],{1,2},3),
            ([0,1,2,3,4,5],{1,4},2),
            ([3,4,5,6,7,8],{4,7},5),
            (list(range(12)),{1,10},2),
        ):
            with self.subTest(cpus=cpus):
                cpu=select_monitor_cpu(cpus)
                self.assertEqual(cpu,want)
                self.assertNotIn(cpu,cm)
                self.assertNotEqual(cpu,select_cpu(cpus))

    def test_exact_four_or_more_without_safety_threshold_changes(self):
        with self.assertRaises(ValueError):
            select_monitor_cpu([0,1,2])
        source=(Path(__file__).resolve().parents[1]/"live"/"d06_gui_cpu_plan.py").read_text()
        self.assertNotIn("CM_TTL_SEC =",source)
        self.assertNotIn("source_timeout",source)
        self.assertNotIn("os.sched_setaffinity",source)
        self.assertNotIn("YES-P2-G07-GOAL",source)

if __name__=="__main__":
    unittest.main()
