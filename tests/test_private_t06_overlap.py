"""Public synthetic tests for private fault JUnit redaction."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from unittest import TestCase
from tempfile import TemporaryDirectory
from private_junit_oracle import assess_fault_overlap

class TestSanitizedFaultDiagnostic(TestCase):
    def test_scan_timeout_precedes_stale_stamp_is_dual_hazard_not_false_pass(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'junit.xml'
            marker='PRIVATE_HIDDEN_STACK_TRACE_SHOULD_NEVER_LEAK'
            path.write_text('<testsuite><testcase><failure message="unexpected stop cause: FAULT:scan_stale">'
                            'unexpected stop cause: FAULT:scan_stale, '
                            "health_diagnostics={'scan_fault_code': 'STALE_STAMP', "
                            "'scan_callback_gaps_over_timeout': 1, 'secret':'" + marker + "'}"
                            '</failure></testcase></testsuite>')
            result=assess_fault_overlap(path)
            self.assertEqual(result['actual_stop_cause'], 'SCAN_STALE')
            self.assertEqual(result['scan_fault_code'], 'STALE_STAMP')
            self.assertEqual(result['callback_deadline'], 'OVERRUN_OBSERVED')
            self.assertNotIn(marker, str(result))
            self.assertFalse(result['gate_accepted'])

    def test_no_deadline_overrun_cannot_claim_dual_hazard(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'junit.xml'
            path.write_text('<testsuite><testcase><failure message="unexpected stop cause: FAULT:scan_stale">'
                            "health_diagnostics={'scan_fault_code': 'STALE_STAMP', 'scan_callback_gaps_over_timeout': 0}"
                            '</failure></testcase></testsuite>')
            self.assertEqual(assess_fault_overlap(path)['callback_deadline'],'NO_OVERRUN_OBSERVED')

    def test_unknown_and_invalid_xml_never_echo_private(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'junit.xml'
            marker='HIDDEN_PRIVATE_ERROR_123'
            path.write_text('<testsuite><testcase><failure message="'+marker+'"/></testcase></testsuite>')
            self.assertEqual(assess_fault_overlap(path)['actual_stop_cause'], 'UNKNOWN')
            self.assertNotIn(marker,str(assess_fault_overlap(path)))
            path.write_text('bad xml')
            self.assertEqual(assess_fault_overlap(path)['actual_stop_cause'], 'UNAVAILABLE')

    def test_scan_invalid_exposes_only_allowed_enum(self):
        with TemporaryDirectory() as d:
            path=Path(d)/'junit.xml'
            path.write_text('<testsuite><testcase><failure>unexpected stop cause: FAULT:scan_invalid '
                            "{'scan_fault_code': 'STALE_STAMP'}"
                            '</failure></testcase></testsuite>')
            result=assess_fault_overlap(path)
            self.assertEqual(result['actual_stop_cause'], 'SCAN_INVALID')
            self.assertEqual(result['scan_fault_code'], 'STALE_STAMP')
            self.assertEqual(result['callback_deadline'], 'UNAVAILABLE')

    def test_missing_file_fails_closed(self):
        self.assertEqual(assess_fault_overlap('/nonexistent/file.xml')['diagnosis'],'NOT_AVAILABLE')
