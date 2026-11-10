"""MVP single consented WSL2 Goal: public contract and real local Git/PTY.

No instructor source, ROS, Gazebo, actual Goal or Fault is run by this test.
"""
from pathlib import Path
import subprocess

from test_p2_remaining_workspace_isolation import simulate, PIN as OLD_SHA, BRANCH as OLD_BRANCH

ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/'scripts/axia_p2_mvp_one_goal_wsl2_once.sh'
PIN='7d61bac6f32e7e205942f3f7cda9cde8c34cbb85'
BRANCH='feature/p2-mvp-one-goal-readiness-20261110'


def run(*args):
    return subprocess.run(['bash',str(WRAPPER),*args],input='',
                          text=True,capture_output=True,timeout=8)


def test_shell_syntax_and_exact_sha():
    subprocess.run(['bash','-n',str(WRAPPER)],check=True,timeout=5)
    src=WRAPPER.read_text()
    assert "readonly SHA='"+PIN+"'" in src
    assert "readonly BRANCH='"+BRANCH+"'" in src
    assert 'p2_owner_l3_wsl2.sh" --case G07' in src
    for required in ('gh auth status','status --porcelain','rev-parse HEAD',
                     'AXIA_P2_OWNER_PINNED_SHA','/dev/tty'):
        assert required in src
    assert 'yes |' not in src.lower()
    assert 'echo YES-' not in src
    assert 'git reset --hard' not in src


def test_self_check_no_goal():
    x=run('--self-check')
    assert x.returncode==0
    assert PIN in x.stdout and 'L3_NOT_RUN' in x.stdout


def test_no_tty_and_unsupported_args_fail_closed():
    assert run().returncode!=0
    for args in (('--case','G06'),('--yes',),('--all',),
                 ('--case','G07'),('--self-check','other')):
        assert run(*args).returncode != 0


def test_actual_shallow_git_clone_and_pty_reaches_only_g07_dummy(tmp_path):
    src=WRAPPER.read_text()
    assert src.count(PIN)==1
    assert src.count(BRANCH)==1
    # Generic real Git+PTY fixture exercises G07-only invocation with locally
    # generated dummy source; it never accesses the instructor repository.
    mocked=tmp_path/'mvp_wrapper.sh'
    mocked.write_text(src.replace(PIN,OLD_SHA).replace(BRANCH,OLD_BRANCH))
    rc,out,records=simulate(tmp_path,wrapper=mocked)
    assert rc==0,out
    assert [x[0] for x in records]==['G07']
    assert 'DIRTY_CASE' not in out
