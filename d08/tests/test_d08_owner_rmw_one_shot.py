"""Owner WSL2 RMW one-shot contract: RED until first timing boundary is joined.

Static/unit fixtures cannot assert WSL2 success; only public L2 and Owner L3
can. NO_GOAL, 500ms, native CM/Guard threshold and original worlds unchanged.
"""
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/scripts"))
from d08_owner_rmw_first_gap import collect_first_scan_boundary, correlate_first_boundary

def test_first_real_violation_selected_over_later_pass(tmp_path):
    root=tmp_path/"run"/"live_evidence"/"owner_replan_cycles"
    for idx,gap in [(0,.505365),(1,.7)]:
        p=root/f"cycle_{idx:04d}";p.mkdir(parents=True)
        (p/"verdict.json").write_text(json.dumps({
            "status":"HOLD",
            "first_scan_timing_boundary":{
                "previous_host_monotonic_sec":100.0+idx*10,
                "current_host_monotonic_sec":100.0+idx*10+gap,
                "receive_gap_sec":gap,
                "header_sim_gap_sec":.102,
                "previous_ros_stamp_ns":12000000000,
                "current_ros_stamp_ns":12102000000}}))
    witness=collect_first_scan_boundary(tmp_path/"run")
    assert witness["kind"]=="ROS_LASERSCAN_FIRST_RECEIVE_GAP"
    assert witness["scope"]=="owner_replan_cycles/cycle_0000"
    assert witness["gap_sec"]==.505365
    assert witness["host_start_sec"]==100.
    assert witness["host_end_sec"]==100.505365

def test_receive_layer_candidate_requires_true_window_bracketing():
    first={"kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP","host_start_sec":10.,
           "host_end_sec":10.55,"gap_sec":.55,"scope":"owner_replan_cycles/cycle_0000"}
    events=[]
    for k in range(7):
        t=9.95+k*.1
        events.append({"direction":"publish","pid":"10","node":"parameter_bridge",
            "host_monotonic_sec":t,"source_timestamp":1000+k})
        events.append({"direction":"take","pid":"20","node":"axia_d08_independent_rx_no_goal",
            "host_monotonic_sec":t+.005,"source_timestamp":1000+k})
    events.extend([
        {"direction":"take","pid":"30","node":"axia_d08_official_physical_replan_no_goal",
         "host_monotonic_sec":9.95,"source_timestamp":1000},
        {"direction":"take","pid":"30","node":"axia_d08_official_physical_replan_no_goal",
         "host_monotonic_sec":10.62,"source_timestamp":1006}
    ])
    v=correlate_first_boundary(first,events,capture_complete=True)
    assert v["cause"]=="UNDETERMINED"
    assert v["candidate"]=="OBSERVER_RMW_RECEIVE_OR_PROCESS_DELAY_CANDIDATE"
    assert v["publisher_window_bracketed"] is True
    assert v["independent_window_bracketed"] is True
    assert v["observer_window_bracketed"] is True
    assert v["first_500ms_violation_retained"] is True

def test_missing_rmw_evidence_fails_closed():
    first={"kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP","host_start_sec":10.,
           "host_end_sec":10.6,"gap_sec":.6,"scope":"owner_replan_cycles/cycle_0000"}
    v=correlate_first_boundary(first,[],capture_complete=False)
    assert v["cause"]=="UNDETERMINED"
    assert v["candidate"]=="EVIDENCE_INCOMPLETE"
    assert v["owner_wsl2_accepted"] is False
    assert v["first_500ms_violation_retained"] is True

def test_original_owner_one_shot_starts_trace_and_archives_small_first_boundary():
    script=(ROOT/"d08/scripts/d08_owner_no_goal_bootstrap.sh").read_text()
    compact=(ROOT/"d08/scripts/d08_compact_evidence.py").read_text()
    trace=(ROOT/"d08/scripts/d08_ros_trace_live_ci.sh").read_text()
    assert "AXIA_D08_TRACE_OUT" in script
    assert "d08_ros_trace_live_ci.sh" in script
    assert "d08_owner_rmw_first_gap.py" in script
    assert "AXIA_D08_NATIVE_RX_PROBE" in script
    assert "AXIA_D08_ROS_ISOLATED_RX_PROBE" in script
    assert "AXIA_D08_TRACE_CAPTURE_MAX_S" in script
    assert "refs/heads/fix/d08-owner-rmw-one-shot-20261119" in script
    assert "'owner_first_gap_verdict.json'" in compact
    assert "'summary.json'" in compact
    assert "'rmw_trace'/f" in compact
    assert "AXIA_D08_TRACE_OUT" in trace
    assert "D08_OWNER_FIRST_BOUNDARY_RMW_CAUSE_UNDETERMINED" in script
    assert "500ms/CM/Guard criterion UNCHANGED" in trace
    for dangerous in ("reset --hard","pkill","rm -rf"):
        assert dangerous not in script


def test_earliest_pregoal_recovery_is_preserved_but_first_live_cycle_is_target(tmp_path):
    root=tmp_path/"run"/"live_evidence"
    root.mkdir(parents=True)
    # CI deliberately stalls the initial executor by 650ms; the first
    # post-initialization violation must NOT be shadowed by this recovery.
    (root/"official_nav2_before_path.json").write_text(json.dumps({
        "real_amcl_and_tf":{"live_scan_odom_at_localization":{
            "no_goal_pre_goal_recovery":{"historical_first_gaps":{
                "scan":{"first_at_host_monotonic":50.7,"gap_sec":.65}}}}}}))
    cycle=root/"owner_replan_cycles"/"cycle_0000"
    cycle.mkdir(parents=True)
    (cycle/"verdict.json").write_text(json.dumps({
        "first_scan_timing_boundary":{
            "previous_host_monotonic_sec":100.0,
            "current_host_monotonic_sec":100.505365,
            "receive_gap_sec":.505365,
            "previous_ros_stamp_ns":48000000000,
            "current_ros_stamp_ns":48102000000}}))
    first=collect_first_scan_boundary(tmp_path/"run")
    assert first["scope"]=="owner_replan_cycles/cycle_0000"
    assert first["gap_sec"]==.505365
    assert first["chronological_first_raw_boundary"]["scope"]=="initial_amcl_pregoal_recovery"
    assert first["initial_pregoal_recovery"]["gap_sec"]==.65
    assert first["selected_for_rmw"]=="FIRST_OFFICIAL_PATH_OR_OWNER_CYCLE"

def test_startup_gap_only_remains_diagnostic_not_stable_cycle_hard_failure(tmp_path):
    root=tmp_path/"run"/"live_evidence"
    root.mkdir(parents=True)
    (root/"official_nav2_before_path.json").write_text(json.dumps({
        "real_amcl_and_tf":{"live_scan_odom_at_localization":{
            "no_goal_pre_goal_recovery":{"historical_first_gaps":{
                "scan":{"first_at_host_monotonic":20.75,"gap_sec":.65}}}}}}))
    first=collect_first_scan_boundary(tmp_path/"run")
    assert first["scope"]=="initial_amcl_pregoal_recovery"
    assert first["selected_for_rmw"]=="ONLY_INITIAL_PREGOAL_RECOVERY"
    script=(ROOT/"d08/scripts/d08_owner_no_goal_bootstrap.sh").read_text()
    assert 'initial_amcl_pregoal_recovery' in script
