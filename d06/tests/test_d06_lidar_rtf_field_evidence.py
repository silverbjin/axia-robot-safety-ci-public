"""Immutable field baseline and controlled Intel/NVIDIA WSLg no-goal comparison."""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d06/tools"))
from axia_d06_lidar_rtf_compare import compare_adapter_results

def report(front,side,rtf,gap,near=0.05):
    return {"schema":"axia_g07_wslg_no_goal_sensor_truth_v1",
      "goal_sent":False,"fixture_moved":False,
      "metrics":{"safety":{"front_median_m":front,
                             "side_median_m":side,
                             "near_ring_fraction_median":near,
                             "max_receipt_gap_sec":gap,
                             "count":60,
                             "clear_count":60 if front>.75 and side>1.2 else 0}},
      "rtf_diagnostics":{"ros_clock_rtf":rtf,
                         "timing_pattern":"SIMULATION_SLOWDOWN_CONSISTENT" if rtf and rtf<.8 else "RTF_NORMAL"}}

class OriginalFieldAndAdapterAB(unittest.TestCase):
    def test_original_intel_rtf_is_not_measured(self):
        e=json.loads((ROOT/"d06/fixtures/g07_wslg_intel_d3d12_rtf_baseline_20261118.json").read_text())
        self.assertEqual(e["safety_scans"],60)
        self.assertEqual(e["all_azimuth_near_ring_fraction"],1.)
        self.assertIsNone(e["ros_clock_rtf"])
        self.assertFalse(e["rtf_ratio_certified"])
        self.assertGreater(e["max_safety_host_receipt_gap_sec"],.3)

    def test_dual_improvement_only_correlation_not_causality(self):
        c=compare_adapter_results(
           report(.525,.63,.30,.789,1.),report(1.41,2.52,.95,.13),
           "D3D12 (Intel(R) Iris(R) Xe Graphics)",
           "D3D12 (NVIDIA GeForce RTX 2060)")
        self.assertEqual(c["result"],"DISTANCE_AND_RTF_BOTH_IMPROVE_CANDIDATE")
        self.assertFalse(c["gpu_causality_proven"])
        self.assertFalse(c["moving_goal_approved"])

    def test_rtf_recovers_but_distance_remains_wrong(self):
        c=compare_adapter_results(
          report(.525,.63,.30,.789,1.),report(.53,.63,.98,.12,1.),
          "D3D12 (Intel Iris Xe)","D3D12 (NVIDIA GeForce RTX 2060)")
        self.assertEqual(c["result"],"RTF_RECOVERED_DISTANCE_STILL_UNSAFE")
        self.assertFalse(c["moving_goal_approved"])

    def test_distance_recovers_but_simulation_stays_slow(self):
        c=compare_adapter_results(
          report(.525,.63,.30,.789,1.),report(1.41,2.52,.34,.75,.05),
          "D3D12 (Intel Iris Xe)","D3D12 (NVIDIA RTX 2060)")
        self.assertEqual(c["result"],"DISTANCE_RECOVERED_RTF_STILL_LOW")

    def test_llvmpipe_or_wrong_selected_adapter_invalidates_comparison(self):
        c=compare_adapter_results(
          report(.525,.63,.30,.789,1.),report(1.41,2.52,.95,.12),
          "D3D12 (Intel Iris Xe)","llvmpipe (LLVM 20.1)")
        self.assertEqual(c["result"],"ADAPTER_COMPARISON_INVALID")
        self.assertFalse(c["gpu_causality_proven"])

    def test_normal_median_but_one_unsafe_scan_must_not_prove_range_recovery(self):
        intel=report(.525,.63,.30,.789,1.)
        nvidia=report(1.41,2.52,.98,.12,.05)
        nvidia["metrics"]["safety"]["clear_count"]=59
        c=compare_adapter_results(intel,nvidia,
            "D3D12 (Intel Iris Xe)", "D3D12 (NVIDIA RTX 2060)")
        self.assertFalse(c["nvidia"]["range_clear"])
        self.assertNotEqual(c["result"],"DISTANCE_AND_RTF_BOTH_IMPROVE_CANDIDATE")
        self.assertFalse(c["moving_goal_approved"])

    def test_absent_original_rtf_prohibits_independent_rtf_conclusion(self):
        c=compare_adapter_results(
          report(.525,.63,None,.789,1.),report(1.41,2.52,.95,.12),
          "D3D12 (Intel Iris Xe)","D3D12 (NVIDIA RTX 2060)")
        self.assertEqual(c["result"],"RTF_AXIS_UNVERIFIED")
        self.assertFalse(c["moving_goal_approved"])

if __name__=="__main__":
    unittest.main()
