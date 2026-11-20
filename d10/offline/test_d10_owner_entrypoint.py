"""Public shell contract only. Uses an intentionally FAKE private instructor checkout.
This cannot validate the actual private D09/D10 Python code or ROS/Gazebo.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent / 'd10_instructor_offline_once.sh'


def make_fake_repo(base: Path):
    repo = base/'fake-instructor'
    block = repo/'training/block_C'
    (block/'fixtures').mkdir(parents=True)
    (block/'day09').mkdir()
    (block/'day10').mkdir()
    (block/'fixtures/generator.py').write_text("print('C01_FIXTURE_CONTRACT_PASS fake_fixture_contract_only')\n",encoding='utf-8')
    (block/'day09/eda_pipeline.py').write_text('''import os,sys
from pathlib import Path
if os.getenv('AXIA_D10_FAKE_C02_FAIL')=='1':
    print('C02_FAKE_FIRST_FAILURE marker=simulated')
    raise SystemExit(42)
out=Path(sys.argv[sys.argv.index('--out')+1]);out.mkdir(parents=True,exist_ok=True)
print('C02_EDA_PASS fake_features_only')
''',encoding='utf-8')
    (block/'day10/isolation_forest_pipeline.py').write_text('''import csv,json,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--out')+1]);out.mkdir(parents=True,exist_ok=True)
m={'source':'SYNTHETIC_COURSE_FIXTURE','train_count':240,'valid_count':80,'test_valid_count':100,'test_invalid_count':4,
 'threshold_source':'normal_valid_only','risk_score_direction':'higher_is_more_anomalous','fit_on_test':False,
 'test_threshold_tuned':False,'ros_actual':False,'gazebo_actual':False,'safety_control_authority':False,
 'confusion':{'TP':1,'FP':2,'FN':17,'TN':80},'threshold':0.10199750}
(out/'if_metrics.json').write_text(json.dumps(m),encoding='utf-8')
with (out/'if_scores_test.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['trace_id','window_id','timestamp_ns','status','truth_label','risk_score','threshold','prediction']);w.writeheader()
    for i in range(100):
        tid='TST_N_00'; win=str(i%10); label='0';pred='NORMAL';stamp=str((i%10)*1000000000+900000000)
        if i==1:tid='TST_A_00';win='5';label='1';pred='WARNING';stamp='5900000000'
        if i==2:tid='TST_A_03';win='9';pred='WARNING';stamp='9900000000'
        if i==3:tid='TST_A_04';win='8';pred='WARNING';stamp='8900000000'
        w.writerow(dict(trace_id=tid,window_id=win,timestamp_ns=stamp,status='VALID',truth_label=label,risk_score='0.1',threshold='0.10199750',prediction=pred))
    for i in range(4):
        w.writerow(dict(trace_id=f'TST_Q_{i:02d}',window_id='0',timestamp_ns='9900000000',status='INSUFFICIENT_DATA',truth_label='-1',risk_score='',threshold='',prediction='INSUFFICIENT_DATA'))
print('C03_IF_PASS fake_model_only')
''',encoding='utf-8')
    subprocess.run(['git','-C',str(repo),'init','-q'],check=True)
    subprocess.run(['git','-C',str(repo),'config','user.name','AXIA CI'],check=True)
    subprocess.run(['git','-C',str(repo),'config','user.email','ci@example.invalid'],check=True)
    subprocess.run(['git','-C',str(repo),'add','.'],check=True)
    subprocess.run(['git','-C',str(repo),'commit','-q','-m','fake fixture for shell contract'],check=True)
    return repo


class EntryPointTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='d10-offline-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.fake=make_fake_repo(self.root)
        self.home=self.root/'somewhere-else';self.home.mkdir()
        self.work=self.root/'out'
        self.env=dict(os.environ,AXIA_D10_INSTRUCTOR_ROOT=str(self.fake),AXIA_D10_WORK_DIR=str(self.work))

    def command(self,mode='--run',env=None):
        return subprocess.run(['bash',str(SCRIPT),mode],cwd=self.home,env=env or self.env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    def test_red_original_command_exits_before_logging(self):
        cmd='set -Eeuo pipefail; test -f day10/isolation_forest_pipeline.py; echo UNREACHABLE'
        p=subprocess.run(['bash','-c',cmd],cwd=self.home,text=True,capture_output=True)
        self.assertEqual(p.returncode,1)
        self.assertNotIn('UNREACHABLE',p.stdout)

    def test_green_doctor_from_home_independent_of_cwd(self):
        p=self.command('--doctor')
        self.assertEqual(p.returncode,0,p.stdout)
        self.assertIn('D10_OWNER_DOCTOR_PASS',p.stdout)
        self.assertIn('D10_INSTRUCTOR_SOURCE_SHA=',p.stdout)
        self.assertNotIn('C03_IF_PASS',p.stdout)

    def test_green_run_from_home_preserves_evidence(self):
        p=self.command()
        self.assertEqual(p.returncode,0,p.stdout)
        self.assertIn('D10_C03_REFERENCE_CONTRACT_PASS',p.stdout)
        self.assertIn('D10_OWNER_OFFLINE_L0_PASS',p.stdout)
        logs=list((self.work/'evidence').glob('run-*/session.log'))
        self.assertEqual(len(logs),1)
        self.assertIn('D10_OWNER_OFFLINE_L0_PASS',logs[0].read_text())
        self.assertTrue((logs[0].parent/'instructor_sha.txt').exists())

    def test_failure_in_c02_has_first_stage_and_session_log(self):
        e=dict(self.env,AXIA_D10_FAKE_C02_FAIL='1')
        p=self.command(env=e)
        self.assertNotEqual(p.returncode,0,p.stdout)
        self.assertIn('D10_OWNER_HOLD',p.stdout)
        self.assertIn('C02_FAKE_FIRST_FAILURE',p.stdout)
        self.assertIn('D10_STAGE=C02_FEATURES',p.stdout)
        self.assertNotIn('D10_STAGE=C03_ISOLATION_FOREST',p.stdout)
        self.assertNotIn('C03_IF_PASS',p.stdout)
        logs=list((self.work/'evidence').glob('run-*/session.log'))
        self.assertTrue(logs)
        self.assertIn('C02_FAKE_FIRST_FAILURE',logs[0].read_text())

    def test_missing_source_does_not_clone_and_reports_stage(self):
        e=dict(self.env,AXIA_D10_INSTRUCTOR_ROOT=str(self.root/'not-existing'),AXIA_D10_DISABLE_CLONE='1')
        p=self.command(env=e)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('D10_SOURCE_BLOCKED',p.stdout)
        self.assertIn('D10_BLOCKED stage=SOURCE_DISCOVERY',p.stdout)
        self.assertTrue(list((self.work/'evidence').glob('run-*/session.log')))

    def test_sourced_script_cannot_enable_strict_mode_in_caller(self):
        p=subprocess.run(['bash','-c',f'set +e; source {str(SCRIPT)!r}; echo CALLER_SURVIVED'],
                         cwd=self.home,text=True,capture_output=True)
        self.assertIn('D10_DO_NOT_SOURCE_USE_BASH_SCRIPT',p.stderr)
        self.assertIn('CALLER_SURVIVED',p.stdout)


    def cold_venv(self):
        """Real Python 3.12 venv deliberately without scikit-learn."""
        if sys.version_info[:2] != (3, 12):
            self.skipTest('Python 3.12 regression runs in CI')
        venv=self.work/'.venv-d10'
        venv.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
        py=venv/'bin/python'
        probe=subprocess.run([str(py),'-c','import sklearn'],capture_output=True,text=True)
        self.assertNotEqual(probe.returncode,0)
        return py

    def test_missing_sklearn_install_disabled_holds_before_model(self):
        self.cold_venv()
        p=self.command(env=dict(self.env,AXIA_D10_AUTO_INSTALL='0'))
        self.assertNotEqual(p.returncode,0,p.stdout)
        self.assertIn('D10_PYTHON_DEPENDENCY_MISSING',p.stdout)
        self.assertIn('D10_BLOCKED stage=PYTHON_DEPENDENCIES',p.stdout)
        self.assertNotIn('D10_STAGE=C01_FIXTURE',p.stdout)
        logs=list((self.work/'evidence').glob('run-*/initial_dependency_error.log'))
        self.assertEqual(len(logs),1,p.stdout)
        self.assertIn('ModuleNotFoundError',logs[0].read_text())

    def test_doctor_missing_sklearn_does_not_install(self):
        self.cold_venv()
        p=self.command('--doctor')
        self.assertNotEqual(p.returncode,0,p.stdout)
        self.assertIn('doctor_only_missing_dependencies',p.stdout)
        self.assertFalse(list((self.work/'evidence').glob('run-*/python_install.log')))

    def test_external_explicit_python_never_mutated(self):
        if sys.version_info[:2]!=(3,12):
            self.skipTest('Python 3.12 regression runs in CI')
        ext=self.root/'external-python'
        subprocess.run([sys.executable,'-m','venv',str(ext)],check=True)
        p=self.command(env=dict(self.env,AXIA_D10_PYTHON=str(ext/'bin/python')))
        self.assertNotEqual(p.returncode,0,p.stdout)
        self.assertIn('explicit_python_missing_dependencies',p.stdout)
        self.assertFalse(list((self.work/'evidence').glob('run-*/python_install.log')))

    def test_missing_sklearn_autoinstall_isolated_venv_and_reuse(self):
        if os.environ.get('AXIA_D10_TEST_AUTO_BOOTSTRAP')!='1':
            self.skipTest('cold venv network test is enabled only in public CI')
        py=self.cold_venv()
        p=self.command()
        self.assertEqual(p.returncode,0,p.stdout)
        self.assertIn('D10_PIP_INSTALL_PASS',p.stdout)
        self.assertIn('D10_OWNER_OFFLINE_L0_PASS',p.stdout)
        logs=list((self.work/'evidence').glob('run-*/python_install.log'))
        self.assertEqual(len(logs),1,p.stdout)
        self.assertEqual(subprocess.run([str(py),'-c','import sklearn,numpy;assert sklearn.__version__=="1.8.0"']).returncode,0)
        doctor=self.command('--doctor')
        self.assertEqual(doctor.returncode,0,doctor.stdout)
        self.assertIn('D10_OWNER_DOCTOR_PASS',doctor.stdout)
        self.assertNotIn('D10_PIP_INSTALL_BEGIN',doctor.stdout)

if __name__=='__main__':
    unittest.main(verbosity=2)
