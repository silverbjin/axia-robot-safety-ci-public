"""AXIA D08 2026-11-18 Owner first Scan/Odom gap: ROS service discovery starvation.

Field evidence: first host receive holes 2.065084s (/scan) and
1.952984s (/odom) while AMCL Pose/TF were actually available.
These tests simulate a 2-second unavailable service at L0 only; fake
callbacks are NEVER counted as actual ROS/Gazebo publisher evidence.
"""
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"harness"))
from d08_amcl_initial_pose import (
    spin_until_initial_pose_service_ready,
    assess_static_amcl_witness,
    summarize_actual_receive_history,
)


class FakeRuntime:
    """Deterministic host clock and two subscribers; no ROS import."""
    def __init__(self):
        self.t=0.0
        self.scan=[(0.0,0)]
        self.odom=[(0.0,0)]
        self.clock=[(0.0,0)]
        self.next_scan=.1
        self.next_odom=.05

    def monotonic(self):
        return self.t

    def spin_once(self, node, timeout_sec):
        assert node is self
        assert 0<timeout_sec<=.050001
        self.t+=timeout_sec
        # Simulated callback *delivery*, not Gazebo publisher validation.
        while self.next_scan<=self.t+1e-8:
            self.scan.append((round(self.t,6),int(self.next_scan*1e9)))
            self.next_scan+=.1
        while self.next_odom<=self.t+1e-8:
            stamp=int(self.next_odom*1e9)
            self.odom.append((round(self.t,6),stamp))
            self.clock.append((round(self.t,6),stamp))
            self.next_odom+=.05


class FakeService:
    def __init__(self, runtime, ready_at):
        self.runtime=runtime
        self.ready_at=ready_at
        self.probes=0

    def service_is_ready(self):
        self.probes+=1
        return self.runtime.t>=self.ready_at-1e-8

    def wait_for_service(self, *args, **kwargs):
        raise AssertionError("D08_REPRO_BLOCKING_WAIT_FOR_SERVICE_CALLED")


def max_gap(events):
    return max(b[0]-a[0] for a,b in zip(events,events[1:]))


def test_delayed_service_discovery_must_continue_scan_odom_callbacks():
    # Old single-thread blocking discovery reproduces ~2s callback holes.
    r=FakeRuntime()
    c=FakeService(r,ready_at=2.)
    result=spin_until_initial_pose_service_ready(
        c,r,r.spin_once,timeout_sec=3.,monotonic=r.monotonic)
    assert result["ready"] is True
    assert 1.99<=result["service_wait_wall_sec"]<=2.06
    assert result["spin_calls"]>=39
    assert result["spin_step_limit_sec"]==.05
    assert len(r.scan)>=20 and len(r.odom)>=40
    assert max_gap(r.scan)<.5 and max_gap(r.odom)<.5
    assert c.probes>=39


def test_real_ros_ci_holdoff_two_seconds_when_service_already_ready():
    # Exact public CI can reproduce a two-second *decision* delay while
    # messages remain actual Gazebo/ROS. L0 here is simulated, never L2.
    r=FakeRuntime()
    c=FakeService(r,ready_at=0.)
    out=spin_until_initial_pose_service_ready(
        c,r,r.spin_once,timeout_sec=3.,min_wait_sec=2.,
        monotonic=r.monotonic)
    assert out["ready"] is True and out["ci_holdoff_sec"]==2.
    assert out["spin_loop_active_during_discovery"] is True
    assert 1.99<=out["service_wait_wall_sec"]<=2.06
    assert max_gap(r.scan)<.5 and max_gap(r.odom)<.5


def test_discovery_timeout_fails_closed_without_suppressing_callbacks():
    r=FakeRuntime()
    c=FakeService(r,ready_at=20.)
    result=spin_until_initial_pose_service_ready(
        c,r,r.spin_once,timeout_sec=.30,monotonic=r.monotonic)
    assert result["ready"] is False
    assert .29<=result["service_wait_wall_sec"]<=.36
    assert result["spin_calls"]>=5
    assert len(r.scan)>=3 and len(r.odom)>=6


def test_real_owner_first_gaps_remain_a_failure_without_verified_recovery():
    witness={
        "amcl_pose":{"frame":"map","stamp_ns":1_602_000_000,
                     "first_source_age_sec":.108,"received_after_request":True},
        "tf":{"frame":"map","child_frame":"base_link",
              "stamp_ns":2_628_000_000,"source":"real_tf2_buffer_lookup"},
        "scan_age_sec":.049586,"odom_age_sec":.001060,
        "scan_stamp_ns":2_502_000_000,"odom_stamp_ns":2_628_000_000,
        "scan_first_gap_over_500ms":{"gap_sec":2.065084,
                                    "first_at_host_monotonic":7563.582062},
        "odom_first_gap_over_500ms":{"gap_sec":1.952984,
                                    "first_at_host_monotonic":7563.618684},
    }
    with pytest.raises(ValueError,match="D08_FIRST_LIVE_SCAN_ODOM_GAP"):
        assess_static_amcl_witness(witness)
    assert witness["scan_first_gap_over_500ms"]["gap_sec"]==2.065084
    assert witness["odom_first_gap_over_500ms"]["gap_sec"]==1.952984


def test_service_discovery_is_spin_driven_not_blocking_or_ttl_relaxed():
    src=(ROOT/"harness/d08_amcl_initial_pose.py").read_text()
    assert "cli.wait_for_service(" not in src
    assert "spin_until_initial_pose_service_ready(" in src
    assert "now-latest[\"scan\"][1]>.5" in src
    assert "now-latest[\"odom\"][1]>.5" in src
    assert "create_publisher(" not in src
    assert "Twist()" not in src


def test_source_stamp_gap_report_is_not_publisher_rmw_verification():
    streams={
       "scan":[(1.,1_000_000_000),(1.1,1_100_000_000),
               (1.3,1_300_000_000)],
       "odom":[(1.,1_000_000_000),(1.05,1_050_000_000),
               (1.1,1_100_000_000)],
       "clock":[(1.,1_000_000_000),(1.05,1_050_000_000),
                (1.1,1_100_000_000)],
    }
    v=summarize_actual_receive_history(streams,now=1.31,started_at=.9)
    assert v["scan"]["max_host_receive_gap_sec"]==.2
    assert v["scan"]["max_source_stamp_delta_sec"]==.2
    assert v["odom"]["max_source_stamp_delta_sec"]==.05
    assert v["publisher_rmw_cadence_measured"] is False
