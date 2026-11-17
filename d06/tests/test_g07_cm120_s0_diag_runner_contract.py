"""Exact future diagnostic one-Goal workflow must not reintroduce S0 failures.

Pure contract: never starts ROS, never sends Goal; no approval implied.
"""
import textwrap
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/axia-g07-cm120-four-gate-one-diagnostic-l2.yml"

class TestS0RuntimeWorkflow(unittest.TestCase):
    def test_reuses_exact_filter_not_unbounded_100k_collector(self):
        s=WF.read_text()
        self.assertIn("from d06.diagnostic.s0_cm_diag_readiness import select_exact_cm_callbacks",s)
        self.assertNotIn("if len(rows)>100000",s)
        self.assertIn("AXIA_G07_S0_ACTUAL_CM_CALLBACK_FILTER_COUNTS",s)
        self.assertIn("ref: ec059007670c0a5c1c13b0fe7d06ad1107f2e1d6",s)

    def test_inline_analyst_python_compiles_and_preload_only_on_child(self):
        s=WF.read_text()
        marker='/usr/bin/python3 - "$RUNNER_TEMP/g07_c05_trace" <<\'PY\''
        self.assertEqual(s.count(marker),1)
        code=s.split(marker,1)[1].split("\n          PY",1)[0]
        compile(textwrap.dedent(code),"<future_C05_G07_exact_TF_analysis>","exec")
        self.assertIn('env LD_PRELOAD="$SO" AXIA_G07_CM120_TF_DIAG_FILE=',s)
        self.assertNotIn('          LD_PRELOAD: /tmp/axia_g07_cm120_abi/',s)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '1'",s)
        self.assertIn("Field 150ms hard safety and 120ms release headroom",s)

if __name__=="__main__":
    unittest.main()
