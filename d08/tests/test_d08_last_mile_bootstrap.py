"""Final D08 user one-goal wrapper pinned exactly to reviewed instructor source."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
WRAPPER=ROOT/'d08/scripts/axia_d08_live_gazebo_wsl2_once.sh'
SHA='99a3a26d787a803f77e94023ca7742518d00a992'

def test_exact_private_revision_and_no_auto_consent():
    src=WRAPPER.read_text()
    assert ("readonly PRIVATE_SHA='"+SHA+"'") in src
    assert "readonly PRIVATE_BRANCH='fix/d08-foot-short-step-owner-20261111'" in src
    # A single-branch shallow clone must refer to the branch that actually
    # contains PRIVATE_SHA; otherwise all WSL2 runs fail after checkout.
    assert '--single-branch --branch "$PRIVATE_BRANCH" --depth 1' in src
    assert "G07_PRIVATE_STOP_043_CONTACT_AND_SHUTDOWN_AUDIT_PREFLIGHT_PASS" in src
    assert "STOP_DISPATCH_M==0.43" in src
    assert "YES-P2-G07-GOAL" in src
    assert "bash --noprofile --norc \"$SRC/instructor/scripts/p2_owner_l3_wsl2.sh\" --case G07 --mvp-one-goal" in src
    assert "echo YES-P2-G07-GOAL" not in src
    assert "AXIA_D08_GAZEBO_GUI=1" in src
    assert "human mesh and G07 Contact proxy share ONE SDF model" in src
    assert "D08_GUI_SHORT_STEP_7CM_6CM_FOOT_VISUAL_ONLY" in src
    assert "D08_FOOT_TUNED_SHORT_STEP_L0_CANDIDATE" in src
    assert "NEW_GAZEBO_L2_AND_OWNER_GUI_STILL_REQUIRED" in src
    assert 'p2_l3_live_session.py' in src
    assert 'py_compile' in src
    # One official ROS-Gazebo image bridge, but SAME 50ms real-D05 gate.
    # The underlying private runner performs the actual bridge.
    assert "D08_PRIVATE_PREFLIGHT_STATIC_PASS" in src
    assert "actor is NOT synchronized" not in src
    assert "AXIA_P2_OWNER_PINNED_SHA" in src
    assert "gh repo clone" in src

def test_syntax_and_static_selfcheck():
    assert subprocess.run(['bash','-n',str(WRAPPER)]).returncode==0
    cp=subprocess.run(['bash',str(WRAPPER),'--self-check'],
                      text=True,capture_output=True,timeout=8)
    assert cp.returncode==0,cp.stderr
    assert SHA in cp.stdout
    assert 'GAZEBO_NOT_RUN' in cp.stdout
