"""Final D08 user one-goal wrapper pinned exactly to reviewed instructor source."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
WRAPPER=ROOT/'d08/scripts/axia_d08_live_gazebo_wsl2_once.sh'
SHA='b5e69e4b221522a79ba38dff42c1f9cb86d1662f'

def test_exact_private_revision_and_no_auto_consent():
    src=WRAPPER.read_text()
    assert ("readonly PRIVATE_SHA='"+SHA+"'") in src
    assert "G07_PRIVATE_STOP_043_CONTACT_AND_SHUTDOWN_AUDIT_PREFLIGHT_PASS" in src
    assert "STOP_DISPATCH_M==0.43" in src
    assert "YES-P2-G07-GOAL" in src
    assert "bash \"$SRC/instructor/scripts/p2_owner_l3_wsl2.sh\" --case G07 --mvp-one-goal" in src
    assert "echo YES-P2-G07-GOAL" not in src
    assert "AXIA_D08_GAZEBO_GUI=1" in src
    assert "AXIA_P2_OWNER_PINNED_SHA" in src
    assert "gh repo clone" in src

def test_syntax_and_static_selfcheck():
    assert subprocess.run(['bash','-n',str(WRAPPER)]).returncode==0
    cp=subprocess.run(['bash',str(WRAPPER),'--self-check'],
                      text=True,capture_output=True,timeout=8)
    assert cp.returncode==0,cp.stderr
    assert SHA in cp.stdout
    assert 'GAZEBO_NOT_RUN' in cp.stdout
