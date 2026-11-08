"""L0 static contract for owner-only one-shot WSL2 workflow. Not a local runtime test."""
from pathlib import Path
import subprocess
import re
ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/"scripts/axia_d04_p1_yolo_wsl2_once.sh"

def test_wsl_script_syntax_and_self_check():
    assert subprocess.run(["bash","-n",str(WRAPPER)],capture_output=True).returncode==0
    r=subprocess.run(["bash",str(WRAPPER),"--self-check"],capture_output=True,text=True)
    assert r.returncode==0 and "CONTRACT_OK" in r.stdout

def test_wsl_exact_source_refs_no_unsafe_goal():
    t=WRAPPER.read_text()
    for keyword in ("653ef49c30973c57a9fcc34b7b2fcc185bc84d95",
        "94d2dd500cb26027ee9c019f4d3a02029ac615cc",
        "AXIA_D04_PUBLIC_SHA","--p1-sha","--waffle","--pi","--world","--actor",
        "--onnx","gh auth status","--display-hold"):
        assert keyword in t,keyword
    assert "send_goal_async(" not in t
    assert "ros2 action send_goal" not in t
    assert "ros2 topic pub /cmd_vel" not in t
    assert "rm -rf --" in t

def test_does_not_auto_merge_or_upload_private_evidence():
    t=WRAPPER.read_text()
    assert "gh pr merge" not in t
    assert "git push" not in t
    assert "gh release create" not in t
    assert re.search(r'G00_G04_ACCEPTED=false',t)
    assert 'AXIA_D04_PUBLIC_SHA must be a pinned commit' in t
