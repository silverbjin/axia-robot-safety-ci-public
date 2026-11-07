import importlib.util
import inspect
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/'scripts/private_pr52_python_ci.py'
s=importlib.util.spec_from_file_location('pr52',FILE)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class TestPrivatePr52PythonCI(unittest.TestCase):
    def test_exact_source_sha_is_hardcoded(self):
        self.assertEqual(m.PIN,'fdf54edf3286d40c1c6338ec0068cf7f9accfefd')
    def test_three_scoped_stages_include_p0_and_full_unit(self):
        self.assertEqual([x[0] for x in m._SUITES],['P0_UNIT','P0_COMPILE','P1_UNIT_ALL'])
        self.assertIn('tests/unit',m._SUITES[2][1])
    def test_sanitized_failure_fingerprint_does_not_echo_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.xml'
            p.write_text('<testsuite><testcase classname="SECRET_CLASS" name="SENSITIVE_CASE">'
                         '<failure type="AssertionError">SECRET_KEY_VALUE</failure>'
                         '</testcase></testsuite>')
            result=m.junit_failure_fingerprints(p)
            self.assertEqual(result['failures'],1)
            self.assertNotIn('SECRET',str(result))
            self.assertEqual(result['failure_categories'][0]['type'],'AssertionError')
    def test_missing_xml_is_blocked_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(m.junit_failure_fingerprints(Path(d)/'absent.xml')['junit_valid'])
    def test_no_goal_fault_or_private_artifact_upload_in_code(self):
        t=FILE.read_text()
        for forbidden in ('ros2 action send_goal','/axia/safety/start',
                          'ros2 topic pub', 'upload-artifact','print(log',
                          "print(raw"):
            self.assertNotIn(forbidden,t)
