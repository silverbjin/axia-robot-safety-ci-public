"""CV2U3T4v owner WSL2 CPU scheduling hypothesis: no-ROS diagnostic contract.

RED before implementing the new standalone diagnostic. Intentional failure on
missing diagnostic code must yield GitHub Actions FAILURE (no false green).
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
ENTRY=ROOT/"scripts/axia_g07_wsl2_cpu_preemption_once.sh"
GUEST=ROOT/"scripts/axia_g07_wsl2_sched_probe.py"
HOST=ROOT/"scripts/axia_g07_windows_host_cpu_probe.ps1"

class TestWSL2CpuPreemptionDiagnostic(unittest.TestCase):
    def test_three_source_files_exist_and_are_valid(self):
        for file in [ENTRY,GUEST,HOST]:
            with self.subTest(path=file.name):
                self.assertTrue(file.is_file())
        subprocess.run(["bash","-n",str(ENTRY)],check=True)
        subprocess.run(["python3","-m","py_compile",str(GUEST)],check=True)

    def test_exact_owner_scenario_is_not_modified_or_autoconsented(self):
        s=ENTRY.read_text()
        self.assertIn("cd8c23c52588f5efd6295b6904e15b1aa54496e7",s)
        self.assertIn("axia_g07_task04_owner_moving_l3_once.sh",s)
        self.assertIn("--self-check",s)
        self.assertIn("--run",s)
        self.assertNotIn("echo YES-P2-G07-GOAL",s)
        self.assertNotIn("pkill -f",s)

    def test_monitor_selftest_contains_synthetic_guest_pause_and_no_host_proof(self):
        p=subprocess.run(["python3",str(GUEST),"selftest"],text=True,
                         capture_output=True,timeout=15)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn("SIMULATED_350MS_GAP_FOUND",p.stdout)
        self.assertIn("HOST_CPU_PREEMPTION_UNCONFIRMED",p.stdout)

    def test_sampler_creates_bounded_valid_samples_with_no_ros(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"guest.jsonl"
            stop=Path(d)/"done"
            p=subprocess.Popen(["python3",str(GUEST),"monitor",
                 "--output",str(out),"--stop",str(stop),
                 "--interval-ms","40"],stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,text=True)
            try:
                import time
                time.sleep(0.4)
                stop.touch()
                stdout,stderr=p.communicate(timeout=5)
            finally:
                if p.poll() is None:
                    p.kill();p.wait()
            self.assertEqual(p.returncode,0,stderr)
            lines=[json.loads(line) for line in out.read_text().splitlines()]
            self.assertGreaterEqual(len(lines),4)
            self.assertTrue(all("mono_ns" in x and "realtime_ns" in x
                                and "gap_ms" in x for x in lines))

    def test_host_guest_and_scan_windows_are_correlated_not_global_max(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location("axia_sched_probe",GUEST)
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Event at guest monotonic 1000.0s, real-time 1800001000.0s.
        base=1800000000
        rows=[{"mono_ns":int(t*1e9),"realtime_ns":int((base+t)*1e9),
               "gap_ms":gap,"steal_jiffies":0,
               "cpu_pressure_some_us":0,"proc_sched":[]}
              for t,gap in [(999.4,40),(999.8,40),(1000.0,350),
                            (1000.3,40),(1001.8,400)]]
        host=[{"epoch_ms":int((base+t)*1000),
               "gap_ms":gap,"host_cpu_pct":cpu}
              for t,gap,cpu in [(999.8,150,92),(1000.05,450,99),
                                (1001.8,800,95)]]
        v={"channel":"scan","first_violation_at":1000.0,
           "first_violation_sec":0.35,"limit_sec":0.3}
        r=mod.evaluate(rows,host,None,{},v)
        self.assertEqual(r["windows_host_max_gap_near_violation_ms"],450)
        self.assertEqual(r["guest_monotonic_max_gap_near_violation_ms"],350)
        self.assertEqual(r["windows_host_cpu_peak_pct_near_violation"],99)
        self.assertEqual(r["hypervisor_cpu_preemption"],
                         "HOST_CPU_PREEMPTION_UNCONFIRMED")

    def test_analyst_does_not_claim_hypervisor_preemption_from_guest_only(self):
        s=GUEST.read_text()
        self.assertIn("HOST_CPU_PREEMPTION_UNCONFIRMED",s)
        self.assertIn("sched_wait_ns",s)
        self.assertIn("steal_jiffies",s)
        self.assertIn("first_timing_violation",s)
        self.assertIn("clock",s.lower())
        self.assertIn("Scan",s)

if __name__=="__main__":unittest.main()
