"""TDD L0: actual runtime failure must never be mistaken for CI package-build PASS."""
from pathlib import Path
import json
import subprocess
import sys
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"scripts/d04_ci_wsl2_diff.py"
spec=importlib.util.spec_from_file_location("d04_ci_wsl2_diff", TARGET)
d=importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def test_all_missing_p1_publishers_is_blocked_not_gui_failure():
    graph={k:{"publishers":[],"subscriptions":[]} for k in d.CMD_TOPICS}
    result=d.inspect_graph(graph)
    assert result["ready"] is False
    assert len(result["topics"])==3
    assert result["topics"]["/cmd_vel"]["publisher_names"]==[]
    assert result["blockers"][0].startswith("P1_COMMAND_GRAPH")


def test_single_collision_monitor_publisher_is_required():
    snapshot={
        "/cmd_vel_smoothed":{"publishers":[{"node_name":"velocity_smoother","topic_type":d.TWIST}],
                             "subscriptions":[{"node_name":"axia_safety_supervisor","topic_type":d.TWIST}]},
        "/cmd_vel_supervised":{"publishers":[{"node_name":"axia_safety_supervisor","topic_type":d.TWIST}],
                               "subscriptions":[{"node_name":"collision_monitor","topic_type":d.TWIST}]},
        "/cmd_vel":{"publishers":[{"node_name":"collision_monitor","topic_type":d.TWIST}],
                     "subscriptions":[{"node_name":"ros_gz_bridge","topic_type":d.TWIST}]}}
    ok=d.inspect_graph(snapshot)
    assert ok["ready"] is True
    snapshot["/cmd_vel"]["publishers"].append({"node_name":"rogue","topic_type":d.TWIST})
    assert d.inspect_graph(snapshot)["ready"] is False


def test_classifies_early_launch_error_without_claiming_causality():
    log="foo\n[ERROR] FileNotFoundError: no such file\n[INFO] stopping\n"
    matches=d.extract_error_lines(log)
    assert any("FileNotFoundError" in s for s in matches)


def test_ci_runtime_gap_always_reported():
    gap=d.ci_scope_gap()
    assert gap["ci_real_p1_runtime"] is False
    assert gap["ci_gazebo_gui"] is False
    assert gap["ci_jazzy_colcon"] is True


def test_readonly_report_with_failed_evidence_and_no_sensor_results(tmp_path):
    evidence=tmp_path/"d04-package-test"
    live=evidence/"live"
    live.mkdir(parents=True)
    (live/"graph_first.json").write_text(json.dumps({
        "graph":{k:{"publishers":[],"subscriptions":[]} for k in d.CMD_TOPICS},
        "verdict":{"passed":False,"reasons":["PUBLISHER_TOPOLOGY:/cmd_vel"]}}))
    (live/"verdict.json").write_text(json.dumps({
        "status":"BLOCKED_OR_INCONCLUSIVE",
        "blocker":"RuntimeError:P1 original graph was not ready",
        "graph_first":{"passed":False}}))
    (live/"package_launch.log").write_text(
        "[ERROR] failed to load launch file: module missing\n")
    (evidence/"owner_summary.json").write_text(json.dumps({"gate_exit":2,"status":"BLOCKED"}))
    output=tmp_path/"report"
    result=d.build_report(evidence,output,collect_host=False)
    assert result["verdict"]["status"]=="BLOCKED_OR_INCONCLUSIVE"
    assert result["graph"]["ready"] is False
    assert result["scope_gap"]["ci_gazebo_gui"] is False
    report=(output/"AXIA_D04_CI_WSL2_DIFF.md").read_text()
    assert "P1_COMMAND_GRAPH" in report
    assert "CI" in report and "WSL2" in report
    assert "모델" in report
    assert (evidence/"owner_summary.json").is_file()
    assert not (evidence/"AXIA_D04_CI_WSL2_DIFF.md").exists()


def test_no_motion_no_sudo_no_upload_and_bounded_process_probes():
    src=TARGET.read_text()
    for banned in ("create_publisher(", "send_goal_async(", "sudo ", "gh pr merge",
                   "git push", "curl ", "requests.post(", "rclone "):
        assert banned not in src
    assert "timeout=" in src
    assert "CASE_NOT_PROVEN" in src
