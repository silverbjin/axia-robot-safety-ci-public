"""D08 static AMCL actual first event/TF readiness regression.

Official Jazzy AMCL publishes Pose on first/resampled filter and may keep
publishing map→odom TF from fresh /scan while stationary. A post-request
one-shot Pose is durable initial localization evidence, not a 10Hz sensor.
L0 values below are contracts only and NOT evidence of real Gazebo L2.
"""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_amcl_initial_pose import assess_static_amcl_witness

def real_witness():
    return {
       "amcl_pose":{"frame":"map","stamp_ns":8_250_000_000,
                    "first_source_age_sec":.08,"received_after_request":True},
       "tf":{"frame":"map","child_frame":"base_link",
             "stamp_ns":9_300_000_000,"source":"real_tf2_buffer_lookup"},
       "scan_age_sec":.12,"odom_age_sec":.04,
       "scan_stamp_ns":9_290_000_000,"odom_stamp_ns":9_310_000_000,
       "scan_first_gap_over_500ms":None,
       "odom_first_gap_over_500ms":None,
    }

def test_static_witness_does_not_demand_second_amcl_pose_after_tf_arrival():
    data=real_witness()
    # Source arrived freshly right after SetInitialPose; real TF came later.
    # Pose need not be REPUBLISHED after TF, unlike a live safety input.
    assert assess_static_amcl_witness(data)["localization_verified"] is True

@pytest.mark.parametrize("change,error",[
    (lambda d:d.pop("amcl_pose"),"FIRST_AMCL_POSE_MISSING"),
    (lambda d:d["amcl_pose"].update(received_after_request=False),"PRE_REQUEST"),
    (lambda d:d["amcl_pose"].update(first_source_age_sec=1.01),"STALE_AT_FIRST_CAPTURE"),
    (lambda d:d["tf"].update(stamp_ns=0),"REAL_TF_MISSING"),
    (lambda d:d.update(scan_age_sec=.501),"LIVE_SCAN_ODOM_STALE"),
    (lambda d:d.update(odom_age_sec=.501),"LIVE_SCAN_ODOM_STALE"),
    (lambda d:d.update(scan_first_gap_over_500ms={"gap":.52}),"FIRST_LIVE_SCAN_ODOM_GAP"),
])
def test_static_amcl_first_event_or_safety_source_fail_closed(change,error):
    x=real_witness();change(x)
    with pytest.raises(ValueError,match=error):
        assess_static_amcl_witness(x)

def test_amcl_real_runtime_never_sends_second_pose_or_mutates_ttls():
    s=(Path(__file__).resolve().parents[1]/"harness"/
       "d08_amcl_initial_pose.py").read_text()
    assert s.count("cli.call_async(req)")==1
    assert "spin_thread=False" in s
    assert "now-latest[\"scan\"][1]>.5" in s
    assert "now-latest[\"odom\"][1]>.5" in s
    assert "cmd_vel" not in s
