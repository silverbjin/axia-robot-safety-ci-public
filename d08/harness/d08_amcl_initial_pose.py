#!/usr/bin/env python3
"""D08 official Nav2 AMCL initialpose: reuse public D07-H01 P0 contract.

Only same-world map-checked localization initialization. No cmd_vel,
NavigateToPose, FollowPath or fabricated map→odom TF.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import time
from collections import deque
from pathlib import Path


def inspect_free_map_pose(msg, x: float, y: float, radius_m=.12) -> dict:
    """Fail closed on unknown/outside/occupied cells around a fixed spawn."""
    info=msg.info
    w,h=int(info.width),int(info.height)
    res=float(info.resolution)
    data=list(msg.data)
    if (msg.header.frame_id!="map" or not w or not h or
        len(data)!=w*h or not math.isfinite(res) or not res>0):
        raise ValueError("D08_AMCL_REAL_MAP_INVALID")
    q=info.origin.orientation
    yaw=math.atan2(2*(q.w*q.z+q.x*q.y),
                    1-2*(q.y*q.y+q.z*q.z))
    if not all(math.isfinite(v) for v in
               (x,y,yaw,info.origin.position.x,info.origin.position.y)):
        raise ValueError("D08_AMCL_MAP_POSE_NONFINITE")
    dx=x-float(info.origin.position.x)
    dy=y-float(info.origin.position.y)
    local_x=math.cos(yaw)*dx+math.sin(yaw)*dy
    local_y=-math.sin(yaw)*dx+math.cos(yaw)*dy
    # Check center plus disk at true map resolution, not an assumed grid.
    cx=math.floor(local_x/res)
    cy=math.floor(local_y/res)
    steps=math.ceil(radius_m/res)
    count=0
    for iy in range(cy-steps,cy+steps+1):
        for ix in range(cx-steps,cx+steps+1):
            if math.hypot((ix+.5)*res-local_x,
                          (iy+.5)*res-local_y)>radius_m+1e-9:
                continue
            if not 0<=ix<w or not 0<=iy<h:
                raise ValueError("D08_AMCL_INITIAL_POSE_MAP_OUTSIDE")
            value=int(data[iy*w+ix])
            if value<0 or value>=50:
                raise ValueError("D08_AMCL_INITIAL_POSE_MAP_NOT_FREE")
            count+=1
    if not count:
        raise ValueError("D08_AMCL_INITIAL_POSE_NO_VALID_GRID_CELLS")
    return {
        "map_frame":"map","spawn_map_xy":[float(x),float(y)],
        "free_checked_cells":count,"resolution_m":res,
        "map_size":[w,h],
        "map_data_sha256":hashlib.sha256(
            bytes(int(v)&0xff for v in data)).hexdigest(),
        "radius_checked_m":radius_m,
        "physical_spawn_from_one_world_launch":True,
        "localization_verified":False,
    }


def summarize_actual_receive_history(streams, *, now, started_at):
    """Read-only provenance of real ROS callbacks, never safety admission.

    Scan/Odom/Clock host receive gaps and sampled sim-time progress are
    distinct from unknown Gazebo publisher/bridge/RMW gaps. This evidence
    survives first-boundary failure as amcl_receive_timing.json.
    """
    report={"status":"D08_REAL_RX_DIAGNOSTIC_NOT_SAFETY_PASS",
            "control_published":False,"goal_sent":False,
            "publisher_rmw_cadence_measured":False,
            "scan_odom_age_limit_sec_unchanged":.5,
            "observed_window_host_sec":round(now-started_at,6)}
    for topic in ("scan","odom","clock"):
        raw=list(streams.get(topic,()))
        gaps=[float(b[0])-float(a[0]) for a,b in zip(raw,raw[1:])]
        sim_progress=((int(raw[-1][1])-int(raw[0][1]))/1e9) if len(raw)>1 else None
        host_progress=(float(raw[-1][0])-float(raw[0][0])) if len(raw)>1 else None
        sample={"callback_count":len(raw),
                "max_host_receive_gap_sec":round(max(gaps),6) if gaps else None,
                "latest_receive_age_sec":round(now-float(raw[-1][0]),6) if raw else None,
                "first_host_receive_sec":round(float(raw[0][0]),6) if raw else None,
                "latest_host_receive_sec":round(float(raw[-1][0]),6) if raw else None,
                "first_sim_stamp_ns":int(raw[0][1]) if raw else None,
                "last_sim_stamp_ns":int(raw[-1][1]) if raw else None,
                "observed_sim_time_progress_sec":round(sim_progress,6) if sim_progress is not None else None,
                "actual_ros_receive_callbacks":True}
        if topic=="clock":
            sample["observed_rtf"]=round(sim_progress/host_progress,6) if host_progress and host_progress>0 else None
        report[topic]=sample
    return report


def assess_pre_goal_receive_recovery(streams, *, started_at, now):
    """Bounded real callback recovery AFTER a NO_GOAL localization warm-up.

    A startup 500ms+ receive gap remains in forensic evidence. Admission
    requires a NEW 1.0s contiguous stream from each of real Scan, Odom and
    Clock, with NO 500ms+ callback gaps, fresh ROS sim stamps and latest
    wall reception <=500ms. This is never a post-Goal safety TTL waiver.
    """
    def blocked(detail):
        raise ValueError("D08_NO_GOAL_RX_NOT_STABLE:"+detail)
    if (not isinstance(streams,dict) or not isinstance(now,(float,int))
            or not isinstance(started_at,(float,int))
            or not all(math.isfinite(v) for v in (now,started_at))
            or not 0<=now-started_at<=45):
        blocked("INVALID_REAL_TIMELINE")
    topics=("scan","odom","clock")
    source={}
    history_gaps={}
    latest_sim_stamps={}
    global_begin=float(started_at)
    for topic in topics:
        raw=streams.get(topic)
        if not isinstance(raw,(list,tuple)) or len(raw)<6:
            blocked(topic.upper()+"_INSUFFICIENT_REAL_CALLBACKS")
        samples=[]
        for sample in raw:
            if (not isinstance(sample,(tuple,list)) or len(sample)!=2
                    or type(sample[0]) not in (int,float)
                    or not math.isfinite(sample[0])
                    or type(sample[1]) is not int or sample[1]<=0):
                blocked(topic.upper()+"_INVALID_CALLBACK")
            samples.append((float(sample[0]),sample[1]))
        if any(b[0]<=a[0] or b[1]<=a[1]
               for a,b in zip(samples,samples[1:])):
            blocked(topic.upper()+"_NONMONOTONIC_CALLBACK_OR_SIM_STAMP")
        first_gap=None
        last_gap_at=None
        for before,after in zip(samples,samples[1:]):
            gap=after[0]-before[0]
            if gap>=.5 and after[0]>=started_at:
                if first_gap is None:
                    first_gap={"gap_sec":round(gap,6),
                               "previous_ros_stamp_ns":before[1],
                               "current_ros_stamp_ns":after[1],
                               "first_at_host_monotonic":round(after[0],6),
                               "publisher_rmw_gap_measured":False}
                last_gap_at=after[0]
        history_gaps[topic]=first_gap
        if last_gap_at is not None:
            global_begin=max(global_begin,last_gap_at)
        source[topic]=samples
        latest_sim_stamps[topic]=samples[-1][1]
    steady={}
    for topic in topics:
        observed=[x for x in source[topic] if x[0]>=global_begin]
        if len(observed)<6:
            blocked(topic.upper()+"_RECOVERY_SAMPLES_MISSING")
        duration=observed[-1][0]-observed[0][0]
        if duration<1.0:
            blocked(topic.upper()+"_RECOVERY_SPAN_TOO_SHORT")
        gaps=[b[0]-a[0] for a,b in zip(observed,observed[1:])]
        if not gaps or max(gaps)>=.5:
            blocked(topic.upper()+"_CONTINUED_RECEIVE_GAP")
        current_age=now-observed[-1][0]
        if not 0<=current_age<=.5:
            blocked(topic.upper()+"_LATEST_CALLBACK_STALE")
        steady[topic]={
            "callback_count":len(observed),
            "steady_span_sec":round(duration,6),
            "maximum_stable_gap_sec":round(max(gaps),6),
            "latest_receive_age_sec":round(current_age,6),
            "latest_ros_stamp_ns":observed[-1][1],
            "actual_ros_callbacks":True}
    for topic in ("scan","odom"):
        sim_age=(latest_sim_stamps["clock"]-latest_sim_stamps[topic])/1e9
        if not -.1<=sim_age<=.5:
            blocked(topic.upper()+"_SIM_STAMP_NOT_CURRENT_WITH_CLOCK")
        steady[topic]["sim_source_age_sec"]=round(sim_age,6)
    return {
        "status":"D08_NO_GOAL_REAL_RX_RECOVERED",
        "goal_sent":False,"control_published":False,
        "limits_unchanged":True,"actual_stream_verified":True,
        "steady_window_start_host_monotonic":round(global_begin,6),
        "minimum_steady_span_sec":1.0,
        "callback_receive_limit_sec":.5,
        "historical_first_gaps":history_gaps,
        **steady,
    }


def assess_static_amcl_witness(witness:dict) -> dict:
    """Validate initial AMCL Pose once, then real *current* scan/odom and TF.

    Official Jazzy AMCL publishes Pose upon initial/resampled filter updates
    but may republish its last map→odom TF on every live LaserScan while
    stationary, without publishing another Pose. This is NOT a relaxation of
    the actual scan/odom/CM safety TTL.
    """
    pose=witness.get("amcl_pose")
    if not isinstance(pose,dict):
        raise ValueError("D08_FIRST_AMCL_POSE_MISSING")
    if pose.get("received_after_request") is not True:
        raise ValueError("D08_AMCL_POSE_PRE_REQUEST")
    age=pose.get("first_source_age_sec")
    if (pose.get("frame")!="map" or
        not isinstance(pose.get("stamp_ns"),int) or pose["stamp_ns"]<=0 or
        not isinstance(age,(float,int)) or not math.isfinite(age) or
        not -.1<=age<=1.0):
        raise ValueError("D08_AMCL_POSE_STALE_AT_FIRST_CAPTURE")
    tf=witness.get("tf")
    if (not isinstance(tf,dict) or tf.get("frame")!="map" or
        tf.get("child_frame")!="base_link" or
        tf.get("source")!="real_tf2_buffer_lookup" or
        not isinstance(tf.get("stamp_ns"),int) or
        tf["stamp_ns"]<=0):
        raise ValueError("D08_REAL_TF_MISSING")
    recovery=witness.get("no_goal_pre_goal_recovery")
    historical_gap=any(
        witness.get(t+"_first_gap_over_500ms") is not None
        for t in ("scan","odom"))
    if historical_gap:
        recovered=(isinstance(recovery,dict)
            and recovery.get("status")=="D08_NO_GOAL_REAL_RX_RECOVERED"
            and recovery.get("goal_sent") is False
            and recovery.get("control_published") is False
            and recovery.get("limits_unchanged") is True
            and recovery.get("actual_stream_verified") is True
            and recovery.get("callback_receive_limit_sec")==.5
            and all(isinstance(recovery.get(t),dict)
                    and recovery[t].get("actual_ros_callbacks") is True
                    and recovery[t].get("callback_count",0)>=6
                    and recovery[t].get("steady_span_sec",0)>=1.0
                    and 0<=recovery[t].get("latest_receive_age_sec",999)<=.5
                    and 0<=recovery[t].get("maximum_stable_gap_sec",999)<.5
                    for t in ("scan","odom","clock")))
        if not recovered:
            raise ValueError("D08_FIRST_LIVE_SCAN_ODOM_GAP")
    for topic in ("scan","odom"):
        age=witness.get(topic+"_age_sec")
        stamp=witness.get(topic+"_stamp_ns")
        if (not isinstance(age,(int,float)) or not math.isfinite(age) or
            not 0<=age<=.5 or not isinstance(stamp,int) or stamp<=0):
            raise ValueError("D08_LIVE_SCAN_ODOM_STALE")
    return {"localization_verified":True,
            "startup_gap_recovered_no_goal":historical_gap,
            "startup_gap_not_l3_safety_pass":True,
            "static_pose_one_shot_not_a_repeating_sensor":True,
            "scan_odom_age_limits_sec":.5,
            "first_amcl_pose_source_age_limit_sec":1.0}


def admit_actual_amcl(node, x: float, y: float, timeout_s=24.0, *, timing_out=None) -> dict:
    """Require actual map, actual scan/odom, AMCL service ACK and map TF."""
    import rclpy
    from rclpy.qos import (
        QoSProfile,DurabilityPolicy,ReliabilityPolicy,qos_profile_sensor_data)
    from rclpy.time import Time
    from nav_msgs.msg import OccupancyGrid,Odometry
    from sensor_msgs.msg import LaserScan
    from rosgraph_msgs.msg import Clock
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from nav2_msgs.srv import SetInitialPose
    from tf2_ros import Buffer,TransformListener,TransformException

    latest={}
    last_arrival={}
    first_safety_gap={}
    # Actual real sensor callback times/stamps, bounded read-only memory.
    # No synthetic ROS message, no safety TTL or Gazebo update-rate change.
    receive_history={k:deque(maxlen=200) for k in ("scan","odom","clock")}
    request_sent_at=[None]
    first_post_request_amcl=[None]
    def stamp_ns(msg):
        return int(msg.header.stamp.sec)*10**9+int(msg.header.stamp.nanosec)
    def recv(kind,msg):
        now=time.monotonic()
        if kind in ("scan","odom") and kind in last_arrival:
            gap=now-last_arrival[kind]
            if gap>=.5 and kind not in first_safety_gap:
                prior=receive_history[kind][-1] if receive_history[kind] else None
                first_safety_gap[kind]={
                    "gap_sec":round(gap,6),
                    "first_at_host_monotonic":round(now,6),
                    "previous_ros_stamp_ns":prior[1] if prior else None,
                    "current_ros_stamp_ns":stamp_ns(msg),
                    "publisher_rmw_gap_measured":False}
        last_arrival[kind]=now
        latest[kind]=(msg,now)
        if kind in receive_history:
            receive_history[kind].append((now,stamp_ns(msg)))
        if (kind=="amcl_pose" and request_sent_at[0] is not None and
            now>=request_sent_at[0] and first_post_request_amcl[0] is None):
            # Sample actual ROS source-time age AT reception. Static AMCL
            # need not publish another Pose after its initial filter update.
            msg_stamp=stamp_ns(msg)
            source_age=(node.get_clock().now().nanoseconds-msg_stamp)/1e9
            first_post_request_amcl[0]={
               "frame":msg.header.frame_id,
               "stamp_ns":msg_stamp,
               "first_source_age_sec":round(source_age,6),
               "received_after_request":True,
               "first_received_host_monotonic":round(now,6)}
            print("D08_AMCL_FIRST_REAL_POST_REQUEST_POSE "+
                  str(first_post_request_amcl[0]),flush=True)
    def receive_clock(msg):
        now=time.monotonic()
        ns=int(msg.clock.sec)*10**9+int(msg.clock.nanosec)
        if ns>0 and (not receive_history["clock"]
                     or ns>receive_history["clock"][-1][1]):
            receive_history["clock"].append((now,ns))
    qos=QoSProfile(depth=1,reliability=ReliabilityPolicy.RELIABLE,
                   durability=DurabilityPolicy.TRANSIENT_LOCAL)
    subs=[
        node.create_subscription(OccupancyGrid,"/map",
             lambda m:recv("map",m),qos),
        node.create_subscription(Odometry,"/odom",
             lambda m:recv("odom",m),qos_profile_sensor_data),
        node.create_subscription(LaserScan,"/scan",
             lambda m:recv("scan",m),qos_profile_sensor_data),
        node.create_subscription(Clock,"/clock",
             receive_clock,qos_profile_sensor_data),
        node.create_subscription(PoseWithCovarianceStamped,"/amcl_pose",
             lambda m:recv("amcl_pose",m),10),
    ]
    # Official AMCL can send the first dynamic map→odom transform directly
    # after SetInitialPose. Subscribe to /tf BEFORE triggering that event:
    # a late TransformListener can miss the only update of a stationary robot.
    # No timeout, safety TTL, fake pose, or transform is modified.
    tfbuf=Buffer()
    listener=TransformListener(tfbuf,node,spin_thread=False)
    deadline=time.monotonic()+timeout_s
    try:
        while (time.monotonic()<deadline
               and not all(k in latest for k in ("map","odom","scan"))):
            rclpy.spin_once(node,timeout_sec=.2)
        if not all(k in latest for k in ("map","odom","scan")):
            raise RuntimeError("D08_AMCL_MAP_SCAN_ODOM_REAL_GRAPH_MISSING")
        now=time.monotonic()
        if (now-latest["scan"][1]>.5 or now-latest["odom"][1]>.5):
            raise RuntimeError("D08_AMCL_SCAN_ODOM_STALE_BEFORE_POSE")
        m=latest["map"][0]
        verdict=inspect_free_map_pose(m,x,y)
        odom=latest["odom"][0]
        scan=latest["scan"][0]
        if (odom.header.stamp.sec<=0 or scan.header.stamp.sec<=0
            or abs(float(odom.twist.twist.linear.x))>.03
            or abs(float(odom.twist.twist.angular.z))>.05):
            raise RuntimeError("D08_AMCL_ODOM_OR_SCAN_INVALID_FOR_P0")
        verdict["odom_frame"]=odom.header.frame_id
        verdict["scan_frame"]=scan.header.frame_id
        verdict["odom_stamp_ns"]=int(odom.header.stamp.sec)*10**9+int(odom.header.stamp.nanosec)
        verdict["scan_stamp_ns"]=int(scan.header.stamp.sec)*10**9+int(scan.header.stamp.nanosec)
        # D07-H01 P0 uses this same official SetInitialPose service contract.
        cli=node.create_client(SetInitialPose,"/set_initial_pose")
        if not cli.wait_for_service(timeout_sec=12):
            raise RuntimeError("D08_AMCL_SET_INITIAL_POSE_SERVICE_MISSING")
        pose=PoseWithCovarianceStamped()
        pose.header.frame_id="map"
        pose.header.stamp=node.get_clock().now().to_msg()
        pose.pose.pose.position.x=float(x)
        pose.pose.pose.position.y=float(y)
        pose.pose.pose.orientation.w=1.
        pose.pose.covariance[0]=.01
        pose.pose.covariance[7]=.01
        pose.pose.covariance[35]=.03
        req=SetInitialPose.Request()
        req.pose=pose
        request_sent_at[0]=time.monotonic()
        pending=cli.call_async(req)
        rclpy.spin_until_future_complete(node,pending,timeout_sec=12)
        if (not pending.done() or pending.exception() is not None
            or pending.result() is None):
            raise RuntimeError("D08_AMCL_SET_INITIAL_POSE_NO_ACK")
        verdict["amcl_service_ack"]=True
        verdict["amcl_service"]="/set_initial_pose"
        verdict["localization_verified"]=False
        # Exact CI-only real ROS Executor pause reproduces WSLg callback
        # starvation without fabricating a message or changing publisher rate.
        # This is an injected test disturbance, NOT a real GPU performance test.
        if (os.environ.get("GITHUB_ACTIONS")=="true" and
            os.environ.get("AXIA_D08_CI_REAL_SUBSCRIBER_PAUSE_SEC")=="0.65"):
            print("D08_CI_REAL_SUBSCRIBER_EXECUTOR_PAUSE_BEGIN_SEC=0.65",flush=True)
            time.sleep(.65)
            verdict["ci_executor_pause_injected_sec"]=.65
        # An AMCL service ACK alone is NOT localization. Require one real
        # post-request, source-fresh AMCL Pose and the *current* real TF2
        # map→base_link chain, plus live fresh Scan/Odom and first gap.
        # Stationary Jazzy AMCL may never republish /amcl_pose despite
        # continuing the live map→odom transform on each fresh LaserScan.
        end=time.monotonic()+18
        last_error="FIRST_AMCL_POSE_OR_REAL_TF_MISSING"
        last_witness={}
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.15)
            first=first_post_request_amcl[0]
            if first is None:
                last_error="FIRST_AMCL_POSE_MISSING"
                continue
            try:
                tf=tfbuf.lookup_transform("map","base_link",Time())
            except TransformException as ex:
                last_error="REAL_TF_NOT_READY:"+str(ex)[:160]
                continue
            now=time.monotonic()
            current_scan=latest.get("scan")
            current_odom=latest.get("odom")
            witness={
                "amcl_pose":first,
                "tf":{"frame":tf.header.frame_id,
                      "child_frame":tf.child_frame_id,
                      "stamp_ns":stamp_ns(tf),
                      "source":"real_tf2_buffer_lookup"},
                "scan_stamp_ns":stamp_ns(current_scan[0]) if current_scan else 0,
                "odom_stamp_ns":stamp_ns(current_odom[0]) if current_odom else 0,
                "scan_age_sec":round(now-current_scan[1],6) if current_scan else None,
                "odom_age_sec":round(now-current_odom[1],6) if current_odom else None,
                "scan_first_gap_over_500ms":first_safety_gap.get("scan"),
                "odom_first_gap_over_500ms":first_safety_gap.get("odom"),
            }
            last_witness=witness
            # A genuine initial no-Goal callback scheduling gap is retained
            # as a first violation. It may be recovered ONLY with new real
            # /scan, /odom and /clock observations for >=1s; no active
            # safety/Goal execution is authorized by this readiness gate.
            if first_safety_gap:
                try:
                    recovery=assess_pre_goal_receive_recovery(
                        receive_history,started_at=request_sent_at[0],now=now)
                except ValueError as exc:
                    last_error=str(exc)
                    last_witness["no_goal_recovery_pending"]=last_error
                    continue
                witness["no_goal_pre_goal_recovery"]=recovery
            try:
                source_check=assess_static_amcl_witness(witness)
            except ValueError as exc:
                last_error=str(exc)
                if "AMCL_POSE_STALE_AT_FIRST_CAPTURE" in last_error:
                    break
                continue
            verdict.update(source_check)
            verdict["amcl_pose_stamp_ns"]=first["stamp_ns"]
            verdict["amcl_pose_source_age_at_first_receive_sec"]=first[
                "first_source_age_sec"]
            verdict["map_base_link_tf_stamp_ns"]=witness["tf"]["stamp_ns"]
            verdict["map_base_link_tf_source"]="real_tf2_buffer_lookup"
            verdict["live_scan_odom_at_localization"]=witness
            if source_check.get("startup_gap_recovered_no_goal"):
                print("D08_FIRST_LIVE_SCAN_ODOM_GAP_RECOVERED_PRE_GOAL_ONLY "+
                      str(witness["no_goal_pre_goal_recovery"]),flush=True)
            print("D08_AMCL_REAL_FIRST_POSE_PLUS_LIVE_TF_READY "+
                  str({"amcl_source_stamp_ns":first["stamp_ns"],
                       "tf_stamp_ns":witness["tf"]["stamp_ns"],
                       "scan_age_sec":witness["scan_age_sec"],
                       "odom_age_sec":witness["odom_age_sec"]}),flush=True)
            return verdict
        diagnostic={"first_amcl_pose":first_post_request_amcl[0],
                    "first_safety_gaps":first_safety_gap,
                    "last_witness":last_witness,
                    "last_error":last_error}
        print("D08_AMCL_REAL_FIRST_WITNESS_HOLD "+str(diagnostic),flush=True)
        raise RuntimeError("D08_AMCL_REAL_MAP_BASE_TF_NOT_READY:"+last_error)
    finally:
        # Preserve actual callback counts/gaps even on a thrown first failure;
        # nobody may promote these diagnostics to a navigation safety PASS.
        report=summarize_actual_receive_history(
            receive_history,now=time.monotonic(),
            started_at=request_sent_at[0] or deadline-timeout_s)
        report["historical_first_receive_gaps"]=first_safety_gap
        report["first_amcl_pose_observed"]=first_post_request_amcl[0]
        if timing_out is not None:
            Path(timing_out).write_text(json.dumps(
                report,indent=2,sort_keys=True)+"\n")
        if any(report[t]["callback_count"]<6 for t in ("scan","odom","clock")):
            print("D08_AMCL_REAL_RX_CADENCE_FIRST_FAILURE "+json.dumps(
                {t:report[t] for t in ("scan","odom","clock")},sort_keys=True),
                flush=True)
        for sub in subs:
            node.destroy_subscription(sub)
