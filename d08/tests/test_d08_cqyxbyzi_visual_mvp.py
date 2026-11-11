"""D08 public contract for the CqYxbyzi field incident (NO ROS or motion).

Verify a shorter visual set_pose jump is requested only for the teacher's
opt-in D08 demonstration; do not publish the instructor's safety code or tests.
The real private Owner branch keeps exact source and its independent tests.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_world import HUMAN_FOOT_RENDER_TUNE_M,HUMAN_VISUAL_LOCAL_Z_M,HUMAN_DAE_MIN_Z_M,HUMAN_SCALE,HUMAN_MODEL_REST_Z_M

def test_foot_visual_only():
    assert HUMAN_FOOT_RENDER_TUNE_M == .06
    assert abs(HUMAN_MODEL_REST_Z_M+HUMAN_VISUAL_LOCAL_Z_M+
               HUMAN_DAE_MIN_Z_M*HUMAN_SCALE-.06)<1e-5

def test_public_wsl2_entrypoint_never_auto_approves_goal():
    src=(ROOT/'d08/scripts/axia_d08_live_gazebo_wsl2_once.sh').read_text()
    assert 'YES-P2-G07-GOAL' in src
    assert 'echo YES-P2-G07-GOAL' not in src
    assert 'AXIA_P2_OWNER_PINNED_SHA' in src
    assert 'gh repo clone' in src
