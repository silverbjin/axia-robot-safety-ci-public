"""RED: D08 Owner 2026-11-18 first /scan 0.819491s /odom 0.752105s gap.

Exact uploaded run source SHA a83629edd71ce51567e184451f2a76bafcf1318b.
This regression is specifically NO_GOAL AMCL warm-up, never accepts a
continuous 0.5s+ safety gap after a Goal or without a true recovery stream.
"""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_amcl_initial_pose import assess_pre_goal_receive_recovery, assess_static_amcl_witness

def event(t,ns):
    return (round(t,6),int(ns))

def recovered():
    # First paired callback holes from genuine Owner archive; subsequent
    # STREAM timestamps model 10Hz scan, 20Hz odom, 20Hz /clock receipts.
    base=28432.08
    scan=[event(base-.819491,1_800_000_000),event(base,1_900_000_000)]
    odom=[event(base-.752105,1_800_000_000),event(base,1_900_000_000)]
    clock=[event(base-.75,1_800_000_000),event(base,1_900_000_000)]
    for i in range(1,15):
        scan.append(event(base+i*.1,1_900_000_000+i*100_000_000))
    for i in range(1,29):
        odom.append(event(base+i*.05,1_900_000_000+i*50_000_000))
        clock.append(event(base+i*.05,1_900_000_000+i*50_000_000))
    return {"scan":scan,"odom":odom,"clock":clock}

def witness():
    return {
       "amcl_pose":{"frame":"map","stamp_ns":1_800_000_000,
                    "first_source_age_sec":.114,"received_after_request":True},
       "tf":{"frame":"map","child_frame":"base_link",
             "stamp_ns":2_808_000_000,"source":"real_tf2_buffer_lookup"},
       "scan_age_sec":.004799,"odom_age_sec":.000381,
       "scan_stamp_ns":2_700_000_000,"odom_stamp_ns":2_808_000_000,
       "scan_first_gap_over_500ms":{"gap_sec":.819491,
           "first_at_host_monotonic":28432.080823},
       "odom_first_gap_over_500ms":{"gap_sec":.752105,
           "first_at_host_monotonic":28432.08484},
    }

def test_real_owner_first_gaps_are_preserved_but_no_goal_recovery_can_prove_stability():
    raw=recovered()
    report=assess_pre_goal_receive_recovery(raw,started_at=28430.0,now=28433.49)
    assert report["status"]=="D08_NO_GOAL_REAL_RX_RECOVERED"
    assert report["historical_first_gaps"]["scan"]["gap_sec"]==.819491
    assert report["historical_first_gaps"]["odom"]["gap_sec"]==.752105
    assert report["scan"]["maximum_stable_gap_sec"]<.5
    assert report["odom"]["maximum_stable_gap_sec"]<.5
    assert report["clock"]["maximum_stable_gap_sec"]<.5
    v=witness();v["no_goal_pre_goal_recovery"]=report
    accepted=assess_static_amcl_witness(v)
    assert accepted["localization_verified"] is True
    assert accepted["startup_gap_recovered_no_goal"] is True
    assert accepted["startup_gap_not_l3_safety_pass"] is True

def test_failed_ongoing_stream_or_clock_stall_must_not_succeed():
    good=recovered()
    # Simulate *continued* post-initial-pose 0.8sec loss, not just
    # one historical WSLg/Gazebo startup scheduling hole.
    bad={k:list(v) for k,v in good.items()}
    bad["scan"][-1]=event(bad["scan"][-2][0]+.81,bad["scan"][-2][1]+100_000_000)
    with pytest.raises(ValueError,match="D08_NO_GOAL_RX_NOT_STABLE"):
        assess_pre_goal_receive_recovery(bad,started_at=28430.,now=bad["scan"][-1][0]+.01)
    bad2={k:list(v) for k,v in good.items()}
    bad2["clock"]=bad2["clock"][:3]
    with pytest.raises(ValueError,match="D08_NO_GOAL_RX_NOT_STABLE"):
        assess_pre_goal_receive_recovery(bad2,started_at=28430.,now=28433.49)
    bad3={k:list(v) for k,v in good.items()}
    bad3["odom"]=[]
    with pytest.raises(ValueError,match="D08_NO_GOAL_RX_NOT_STABLE"):
        assess_pre_goal_receive_recovery(bad3,started_at=28430.,now=28433.49)

def test_no_gap_history_cannot_be_forged_into_safety_pass():
    v=witness()
    with pytest.raises(ValueError,match="D08_FIRST_LIVE_SCAN_ODOM_GAP"):
        assess_static_amcl_witness(v)
    v["no_goal_pre_goal_recovery"]={"status":"D08_NO_GOAL_REAL_RX_RECOVERED"}
    with pytest.raises(ValueError,match="D08_FIRST_LIVE_SCAN_ODOM_GAP"):
        assess_static_amcl_witness(v)
    # Historic violation after Goal is never covered by this preflight.
    v["no_goal_pre_goal_recovery"]={
        "status":"D08_NO_GOAL_REAL_RX_RECOVERED",
        "goal_sent":True,"control_published":False,
        "limits_unchanged":True,"actual_stream_verified":True}
    with pytest.raises(ValueError,match="D08_FIRST_LIVE_SCAN_ODOM_GAP"):
        assess_static_amcl_witness(v)
