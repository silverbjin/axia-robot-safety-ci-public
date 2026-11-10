"""D08 public contract only; never starts a Goal on a CI runner."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
WRAPPER=ROOT/'d08/scripts/axia_d08_live_gazebo_wsl2_once.sh'

def test_d08_owner_requires_real_terminal_and_private_pinned_checkout():
    text=WRAPPER.read_text()
    assert "YES-P2-G07-GOAL" in text
    assert "AXIA_D08_GAZEBO_GUI=1" in text
    assert "AXIA_P2_OWNER_PINNED_SHA" in text
    assert "--case G07 --mvp-one-goal" in text
    assert "status --porcelain" in text
    assert "gh repo clone" in text
    assert "sha256sum -c" in text
    assert "AXIA_D04_REPEAT=1" in text
    assert "silverbjin/axia-robot-safety-instructor" in text
    assert "YES-P2-G07-GOAL\n" not in text  # no auto-writing consent response

def test_d08_owner_script_syntax_and_static_report():
    assert subprocess.run(['bash','-n',str(WRAPPER)]).returncode==0
    r=subprocess.run(['bash',str(WRAPPER),'--self-check'],
          text=True,capture_output=True,timeout=10)
    assert r.returncode==0,r.stderr
    assert 'D08_LIVE_WRAPPER_STATIC_PASS' in r.stdout
    assert 'GAZEBO_NOT_RUN' in r.stdout
