"""Public-only fast diagnostics and bounded private log reader tests."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from private_nav2_phase_smoke1 import tail_private_log

class TestBoundedLogReader(unittest.TestCase):
    def test_tails_large_file_without_emitting_private_text(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'private_launch.log'
            p.write_bytes(b'A'*100+b'[lifecycle_manager_localization]: Shutting down managed nodes...')
            text,status=tail_private_log(p,max_bytes=70)
            self.assertEqual(status,'TAIL_READ')
            self.assertNotIn('A'*50,text)
            self.assertTrue(text.endswith('Shutting down managed nodes...'))
    def test_missing_and_invalid_max_is_fail_closed(self):
        self.assertEqual(tail_private_log(Path('/never/exists'))[1],'LOG_MISSING')
        self.assertEqual(tail_private_log(Path('/never/exists'),max_bytes=-1)[1],'INVALID_BOUND')
