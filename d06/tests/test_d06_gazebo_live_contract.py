"""D06 classroom Gazebo GUI/RViz source contract (no ROS control)."""
import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
D06=ROOT/"d06"
W=D06/"scripts/d06_gazebo_rviz_owner_wsl2_once.sh"
S=D06/"scripts/d06_rviz_sidecar.sh"
M=D06/"live/d06_readonly_monitor.py"
R=D06/"rviz/d06_safety_bubble.rviz"
G=D06/"docs/D06_GAZEBO_RVIZ_OWNER_GUIDE_KO.md"

def test_reuse_pinned_owner_and_keep_tty_goal_consent():
    src=W.read_text()
    for token in ("d1769b8675c85e7ee564966637cef9113435904a",
        "afe4e9ae3f6542ef7b2bd3097ce5c15ae5a5ddcc",
        "axia_p4_g11_owner_g07_rmw_provenance_once.sh",
        "YES-P2-G07-GOAL","AXIA_P2_OWNER_PINNED_SHA",
        "gh auth status","--self-check","D06_GAZEBO_GUI_NOT_YET_VERIFIED"):
        assert token in src,token
    assert "AXIA_G07_CI_SIM_GOAL_ALLOWED=1" not in src
    assert "echo YES-P2-G07-GOAL" not in src

def test_rviz_sidecar_binds_exact_new_owner_session_and_cleans_up():
    src=S.read_text()
    for token in ("session.env","-newer","ROS_DOMAIN_ID",
      "rviz2 -d","d06_readonly_monitor.py","D06_RVIZ_STARTED",
      "D06_GUI_NOT_ACCEPTANCE"):
        assert token in src,token

def test_rviz_displays_actual_scan_odom_tf_robot_and_visual_markers():
    src=R.read_text()
    for token in ("Fixed Frame: odom","/scan","/odom","/robot_description",
      "rviz_default_plugins/TF","rviz_default_plugins/MarkerArray",
      "/axia/d06/rviz/bubble"):
        assert token in src,token
    assert "/cmd_vel" not in src

def test_monitor_does_not_publish_robot_control():
    src=M.read_text()
    ast_tree=ast.parse(src)
    pub_calls=[n for n in ast.walk(ast_tree)
       if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
       and n.func.attr=="create_publisher"]
    assert len(pub_calls)==1
    assert "MarkerArray" in ast.unparse(pub_calls[0])
    assert "/axia/d06/rviz/bubble" in ast.unparse(pub_calls[0])
    for forbidden in ("send_goal_async(","create_client(","create_publisher(Twist",
                      "AXIA_G07_CI_SIM_GOAL_ALLOWED=1"):
        assert forbidden not in src
    for status in ("CLEAR","SLOWDOWN","STOP","UNKNOWN","EVIDENCE_ONLY_NOT_CM_VERDICT"):
        assert status in src

def test_classroom_procedure_has_evidence_boundaries_and_shutdown():
    src=G.read_text()
    for token in ("--self-check","rviz2","Gazebo","YES-P2-G07-GOAL",
      "RED","GREEN","CI","WSL2","Ctrl+C","EVIDENCE=",
      "NOT_RUN","UNKNOWN","SW Stop","E-Stop","L1","L2","L3","main 병합"):
        assert token in src,token


def test_gui_sidecar_failure_is_never_reported_as_success_and_reap_is_bounded():
    wrapper=W.read_text()
    sidecar=S.read_text()
    assert "D06_RVIZ_NOT_CONFIRMED" in wrapper
    # Original G07 success must not hide missing RViz startup or early child exit.
    assert "D06_RVIZ_SIDECAR_EXITED_BEFORE_OWNER_COMPLETION" in wrapper
    assert "rc=3" in wrapper
    # Cleanup must not block forever and must signal only sidecar-owned groups.
    assert 'kill -KILL -- "-$pid"' in sidecar
    assert 'wait "$pid"' in sidecar
