"""RED: past WSL2 Owner evidence proved 1.46s Goal and 3.03s set_pose ACK.

One Goal must preload SlowZone before Goal and shrink the demo-only Goal
tolerance; do not weaken any formal G07 acceptance or automate consent.
"""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/'scripts/axia_p2_mvp_one_goal_wsl2_once.sh'
PRIVATE_SHA='1526fba4675aeaac3c09a23f820cb916e7d4ac1e'
PRIVATE_BRANCH='fix/p2-mvp-one-goal-timing-20261110'


def test_owner_bootstrap_pins_revised_mvp_and_invokes_only_approved_case():
    s=WRAPPER.read_text()
    assert "readonly SHA='"+PRIVATE_SHA+"'" in s
    assert "readonly BRANCH='"+PRIVATE_BRANCH+"'" in s
    assert 'p2_owner_l3_wsl2.sh" --case G07 --mvp-one-goal' in s
    assert 'YES-P2-G07-GOAL' in s
    assert 'gh auth status' in s
    assert 'rev-parse HEAD' in s and 'status --porcelain' in s
    assert 'AXIA_P2_OWNER_PINNED_SHA' in s
    assert 'yes |' not in s.lower()
    assert 'echo YES-' not in s
    assert 'git reset --hard' not in s
    subprocess.run(['bash','-n',str(WRAPPER)],check=True)


def test_self_check_does_not_send_any_goal():
    result=subprocess.run(['bash',str(WRAPPER),'--self-check'],
                          capture_output=True,text=True,timeout=8)
    assert result.returncode==0
    assert PRIVATE_SHA in result.stdout
    assert 'L3_NOT_RUN' in result.stdout
