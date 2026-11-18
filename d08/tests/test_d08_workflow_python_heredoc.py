"""Exact regression: #44207752810 accidentally nested shell command in Python heredoc.

Compile YAML's embedded Python sections statically; ROS/Gazebo NOT RUN.
"""
from pathlib import Path
import textwrap

WF = Path(__file__).resolve().parents[2] / ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"

def test_every_workflow_inline_python_heredoc_is_syntax_valid():
    src=WF.read_text().splitlines()
    fragments=[]
    body=None
    for line in src:
        if body is None:
            if line.strip() in ("python3 - <<'PY'", "python - <<'PY'"):
                body=[]
        elif line.strip()=="PY":
            fragments.append(body)
            body=None
        else:
            body.append(line)
    assert body is None, "D08_WORKFLOW_PY_HEREDOC_UNCLOSED"
    assert len(fragments)>=4
    for i,lines in enumerate(fragments):
        text=textwrap.dedent("\n".join(lines))+"\n"
        compile(text,f"<d08 workflow python block {i+1}>","exec")

def test_second_official_nav2_simulation_is_outside_prior_python_inline_verdict():
    s=WF.read_text().splitlines()
    nav=next(i for i,line in enumerate(s) if '--official-nav2' in line)
    before=[i for i,line in enumerate(s[:nav]) if line.strip()=="PY"]
    next_cmd=[i for i,line in enumerate(s[nav+1:],start=nav+1) if line.strip()=="python3 - <<'PY'"]
    assert before and next_cmd and before[-1]<nav<next_cmd[0]
    assert "D08_OFFICIAL_NAV2_SAME_WORLD_BEFORE_PATH_L2_PASS_NO_GOAL" in "\n".join(s)
