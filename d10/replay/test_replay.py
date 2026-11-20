"""Public educational replay regression; tests do not contain instructor model/score answers."""
import csv
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('d10_replay_builder', HERE/'build_replay.py')


def builder():
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_public_smoke_scores(raw_path: Path, manifest_path: Path, target: Path):
    """Independent UI-only synthetic scores, not Isolation Forest predictions."""
    with raw_path.open(newline='', encoding='utf-8') as f:
        raw = list(csv.DictReader(f))
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    grouped = {}
    for x in raw: grouped.setdefault(x['trace_id'], []).append(x)
    header = ['trace_id','window_id','timestamp_ns','status','quality_reason','truth_label','risk_score','threshold','prediction']
    with target.open('w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator='\n');w.writeheader()
        for tid, rows in grouped.items():
            if tid in manifest['quality_cases']:
                w.writerow(dict(trace_id=tid,window_id='0',timestamp_ns=rows[-1]['timestamp_ns'],
                    status='INSUFFICIENT_DATA',quality_reason=manifest['quality_cases'][tid],truth_label='-1',
                    risk_score='',threshold='',prediction='INSUFFICIENT_DATA'))
            else:
                for index in range(10):
                    window=rows[index*10:(index+1)*10]
                    # Purposefully alter class counts versus baseline so renderer cannot hardcode answers.
                    risk=0.3 if index==6 and tid=='TST_A_02' else 0.02
                    w.writerow(dict(trace_id=tid,window_id=str(index),timestamp_ns=window[-1]['timestamp_ns'],
                        status='VALID',quality_reason='',truth_label=window[-1]['truth_label'],
                        risk_score=f'{risk:.8f}',threshold='0.10000000',
                        prediction='WARNING' if risk>0.1 else 'NORMAL'))


class ReplayContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(__import__('os').environ['AXIA_D10_PUBLIC_FIXTURE_DIR'])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)
        self.raw=self.fixture/'test_mixed.csv'
        self.manifest=self.fixture/'scenario_manifest.json'
        self.score=self.path/'smoke_scores.csv'
        write_public_smoke_scores(self.raw,self.manifest,self.score)
        self.mod=builder()

    def test_public_smoke_renders_one_self_contained_html(self):
        payload=self.mod.validate_and_build(self.raw,self.score,self.manifest,'CI_SMOKE_NOT_MODEL')
        out=self.path/'demo.html'
        self.mod.render_html(payload,out)
        html=out.read_text(encoding='utf-8')
        self.assertIn('OFFLINE RECORDED REPLAY',html)
        self.assertIn('CI_SMOKE_NOT_MODEL',html)
        self.assertIn('TST_A_02',html)
        self.assertIn('INSUFFICIENT_DATA',html)
        self.assertIn('정답 공개',html)
        self.assertIn('AI 판정',html)
        self.assertIn('<canvas',html)
        self.assertNotIn('https://',html)
        self.assertNotIn('fetch(',html)
        self.assertNotIn('send_goal_async',html)
        self.assertEqual(len(payload['traces']),14)
        self.assertEqual(payload['confusion'],{'TP':1,'FP':0,'FN':17,'TN':82})

    def test_generated_javascript_is_syntax_valid(self):
        node=shutil.which('node')
        if not node:
            self.fail('Node.js is required for JavaScript syntax CI verification')
        payload=self.mod.validate_and_build(self.raw,self.score,self.manifest,'CI_SMOKE_NOT_MODEL')
        out=self.path/'demo.html';self.mod.render_html(payload,out)
        text=out.read_text(encoding='utf-8')
        js=text.split('<script>',1)[1].split('</script>',1)[0]
        file=self.path/'demo.js';file.write_text(js,encoding='utf-8')
        result=subprocess.run([node,'--check',str(file)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_score_window_time_mismatch_fail_closed(self):
        s=self.score.read_text(encoding='utf-8').replace('TST_A_02,6,6900000000', 'TST_A_02,6,6800000000')
        self.score.write_text(s,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'timestamp'):
            self.mod.validate_and_build(self.raw,self.score,self.manifest,'CI_SMOKE_NOT_MODEL')

    def test_invalid_trace_must_never_be_scored(self):
        s=self.score.read_text(encoding='utf-8').replace('INSUFFICIENT_DATA,MISSING_VALUE,-1,,,INSUFFICIENT_DATA',
               'INSUFFICIENT_DATA,MISSING_VALUE,-1,0.00000000,0.10000000,NORMAL')
        self.score.write_text(s,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'quality'):
            self.mod.validate_and_build(self.raw,self.score,self.manifest,'CI_SMOKE_NOT_MODEL')

    def test_prediction_disagreement_fail_closed(self):
        s=self.score.read_text(encoding='utf-8').replace('0.30000000,0.10000000,WARNING',
               '0.30000000,0.10000000,NORMAL')
        self.score.write_text(s,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'prediction'):
            self.mod.validate_and_build(self.raw,self.score,self.manifest,'CI_SMOKE_NOT_MODEL')

    def test_model_scores_are_not_derived_from_labels(self):
        payload=self.mod.validate_and_build(self.raw,self.score,self.manifest,'CI_SMOKE_NOT_MODEL')
        anomaly=next(x for x in payload['traces'] if x['id']=='TST_A_02')
        self.assertEqual(anomaly['windows'][6]['prediction'],'WARNING')
        self.assertEqual(anomaly['windows'][4]['prediction'],'NORMAL')
        self.assertEqual(payload['source'],'SYNTHETIC_COURSE_FIXTURE')
        self.assertFalse(payload['ros_actual'])
        self.assertFalse(payload['safety_control_authority'])


if __name__=='__main__':unittest.main()
