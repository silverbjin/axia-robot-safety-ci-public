#!/usr/bin/env python3
"""Read-only D08 physical-person three-phase official Nav2 Path observation.

ONE already-running real Gazebo+Waffle+AMCL world. No robot Goal, Twist,
fake /scan, fake Costmap, custom Planner or changed safety TTL.
D07-H01 L2 world/map coordinates are *candidates*, not evidence for D08.
"""
from __future__ import annotations

from collections import deque
from d08_scan_gap_trace import (first_scan_receive_gap, diagnose_first_receive_boundary,
                                compare_native_scan_first_gap,
                                diagnose_native_clock_during_first_gap,
                                compare_isolated_ros_first_gap,
                                compare_worst_scan_pair_receivers,
                                scan_gap_operation_overlaps,
                                analyze_process_heartbeat_gap)
import json
import math
from pathlib import Path
import re
import subprocess
import threading
import time

# Exact verified D07-H01 public real Gazebo run #44051183220 (NOT D08 proof).
GOAL_MAP = (-1.7, 0.7)
CANDIDATE_MAP = (-1.9686799503482275, 0.1702990252746351)
NEAR_WORLD = (-1.9791189342778877, 0.17129139623634398, 0.24)
FAR_WORLD = (-0.58, -0.5, 0.24)
START_MAP = (-2.0, -0.5)


def _stamp(m) -> float:
    return m.header.stamp.sec + m.header.stamp.nanosec * 1e-9


def _path_distance_to_point(poses, point):
    """True polyline-to-obstacle distance, not path length or set_pose guess."""
    if len(poses) < 3:
        raise ValueError("D08_OFFICIAL_PATH_TOO_SHORT")
    best = math.inf
    for a, b in zip(poses, poses[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        denom = dx * dx + dy * dy
        t = max(0.0, min(1.0,
            ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / denom
        )) if denom > 0 else 0
        best = min(best, math.hypot(a[0] + t * dx - point[0],
                                    a[1] + t * dy - point[1]))
    return best


def _lethal_near(msg, xy=CANDIDATE_MAP, radius=.28):
    """Native ROS OccupancyGrid obstacle data from official global Costmap."""
    if msg.header.frame_id != "map":
        raise ValueError("D08_NATIVE_COSTMAP_FRAME_NOT_MAP")
    info = msg.info
    res = float(info.resolution)
    if res <= 0 or len(msg.data) != info.width * info.height:
        raise ValueError("D08_NATIVE_COSTMAP_GEOMETRY_INVALID")
    q = info.origin.orientation
    yaw = math.atan2(2*(q.w*q.z + q.x*q.y),
                      1-2*(q.y*q.y + q.z*q.z))
    dx,dy = xy[0] - info.origin.position.x, xy[1] - info.origin.position.y
    lx = math.cos(yaw) * dx + math.sin(yaw) * dy
    ly = -math.sin(yaw) * dx + math.cos(yaw) * dy
    ix,iy = math.floor(lx/res),math.floor(ly/res)
    extent = math.ceil(radius/res)
    count = 0
    for y in range(max(0,iy-extent),min(info.height,iy+extent+1)):
        for x in range(max(0,ix-extent),min(info.width,ix+extent+1)):
            if math.hypot((x+.5)*res-lx,(y+.5)*res-ly) <= radius:
                if msg.data[y*info.width+x] >= 99:
                    count += 1
    return count


def evaluate_three_phases(rows: list[dict], scan_receive_gaps: list[float]) -> dict:
    """Fail-closed lightweight TDD contract, not synthetic sensor admission."""
    if [r.get("stage") for r in rows] != ["before","intrusion","restored"]:
        raise ValueError("D08_THREE_OFFICIAL_PATH_PHASES_REQUIRED")
    if any(r.get("source") != "official_compute_path_to_pose"
           or r.get("frame") != "map"
           or r.get("goal_sent") is not False
           or len(r.get("poses", [])) < 3
           or r.get("scan_stamp",0) <= 0
           or r.get("costmap_stamp",0) <= 0
           or not r.get("gazebo_native_ack",False) for r in rows):
        raise ValueError("D08_REAL_PATH_OR_SCAN_COSTMAP_PROVENANCE_MISSING")
    if any(rows[i]["scan_stamp"] <= rows[i-1]["scan_stamp"] or
           rows[i]["costmap_stamp"] <= rows[i-1]["costmap_stamp"]
           for i in (1,2)):
        raise ValueError("D08_STALE_REAL_SCAN_OR_COSTMAP_PHASE")
    if rows[1].get("lethal_near",0) < rows[0].get("lethal_near",0)+3:
        raise ValueError("D08_REAL_COSTMAP_OBSTACLE_NOT_MARKED")
    if rows[2].get("lethal_near",999) > rows[0].get("lethal_near",0):
        raise ValueError("D08_REAL_COSTMAP_OBSTACLE_NOT_CLEARED")
    near_delta = rows[1]["path_distance_from_obstacle_m"] - rows[0]["path_distance_from_obstacle_m"]
    restore_delta = abs(rows[2]["path_distance_from_obstacle_m"] -
                        rows[0]["path_distance_from_obstacle_m"])
    if near_delta < .15:
        raise ValueError("D08_OFFICIAL_PATH_DETOUR_NOT_OBSERVED")
    if restore_delta > .12:
        raise ValueError("D08_OFFICIAL_PATH_RESTORATION_NOT_OBSERVED")
    if len(scan_receive_gaps) < 3:
        raise ValueError("D08_REAL_SCAN_CADENCE_NOT_MEASURED")
    first_gap = next((dict(index=i+1,gap_sec=round(g,6))
                      for i,g in enumerate(scan_receive_gaps) if g > .5), None)
    if first_gap:
        raise ValueError("D08_FIRST_REAL_SCAN_RECEIVE_GAP_OVER_500MS:"+json.dumps(first_gap))
    return {"status":"D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL",
            "detour_delta_m":round(near_delta,5),
            "restore_delta_m":round(restore_delta,5),
            "scan_wall_gap_max_sec":round(max(scan_receive_gaps),6),
            "first_scan_gap_violation":None,"robot_moving_goal_sent":False,
            "actual_cm_safety_ttl_proven":False}


def cm_state_is_active(state_id:int, state_label:str)->bool:
    """Native lifecycle state is sufficient only on the exact active tuple."""
    return state_id==3 and state_label=="active"


def assess_official_cm_native_scan(state_id:int, state_label:str,
                                   observation_sources:list, scan_topic:str)->dict:
    """Scoped proof from *real official* CM lifecycle/get_parameters services.

    This verifies the active configured scan source only. It does not
    fabricate collision_monitor internal callback gaps or STOP/SLOW actions
    when the stationary Waffle has no cmd_vel inputs.
    """
    if not cm_state_is_active(state_id,state_label):
        raise ValueError("D08_OFFICIAL_CM_NOT_ACTIVE")
    if ("scan" not in observation_sources):
        raise ValueError("D08_OFFICIAL_CM_SCAN_SOURCE_MISSING")
    if scan_topic not in ("scan","/scan"):
        raise ValueError("D08_OFFICIAL_CM_SCAN_TOPIC_NOT_REAL")
    return {"official_cm_active_scan_configured":True,
            "cm_native_lifecycle_state":"active",
            "cm_scan_source_name":"scan",
            "cm_actual_configured_scan_topic":scan_topic,
            "cm_internal_receive_gap_verified":False,
            "cm_action_state_verified":False,
            "moving_goal_sent":False}


INDEPENDENT_RX_HISTORY_LIMIT = 4096


def new_independent_rx_buffers():
    """Keep a ~9s 250Hz clock window without unbounded trace growth."""
    return {k:deque(maxlen=INDEPENDENT_RX_HISTORY_LIMIT)
            for k in ("scan","odom","clock","tf")}


def run(out:Path, env:dict, source_sha:str, timeout_s=35.) -> int:
    import rclpy
    from rclpy.action import ActionClient
    from rclpy.executors import MultiThreadedExecutor, SingleThreadedExecutor
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from rclpy.qos import (qos_profile_sensor_data, QoSProfile,
                            ReliabilityPolicy, DurabilityPolicy)
    from rclpy.time import Time
    from nav_msgs.msg import OccupancyGrid, Odometry, Path as NavPath
    from sensor_msgs.msg import LaserScan
    from rosgraph_msgs.msg import Clock
    from tf2_msgs.msg import TFMessage
    from nav2_msgs.action import ComputePathToPose
    from lifecycle_msgs.srv import GetState
    from rcl_interfaces.srv import GetParameters
    from action_msgs.msg import GoalStatus
    from geometry_msgs.msg import PoseStamped
    from tf2_ros import Buffer, TransformListener, TransformException

    if not re.fullmatch("[0-9a-f]{40}",source_sha):
        raise ValueError("D08_SOURCE_SHA_REQUIRED")
    out=Path(out)
    if out.exists():
        raise ValueError("D08_PATH_PHASE_OUTPUT_EXISTS")
    out.mkdir(parents=True)
    result={"status":"HOLD","source_sha":source_sha,
            "goal_sent":False,"cmd_vel_published":False,
            "fake_scan_published":False,
            "reused_d07_coordinates_are_candidates_only":True,
            "official_nav2_action":"/compute_path_to_pose",
            "scene":"same_robot_same_person_same_world_one_process",
            "ros_domain_id":env.get("ROS_DOMAIN_ID"),
            "gz_partition":env.get("GZ_PARTITION")}
    rows=[]
    scan_rows=deque(maxlen=600)
    costmap_rows=deque(maxlen=250)
    odom_rows=deque(maxlen=250)
    callbacks_lock=threading.Lock()
    rclpy.init()
    node=Node("axia_d08_official_physical_replan_no_goal",
         parameter_overrides=[Parameter("use_sim_time",value=True)],
         automatically_declare_parameters_from_overrides=True)
    # Display only the ORIGINAL official Nav2 Path in RViz; no planner,
    # controller or cmd_vel publisher is created by this observer.
    path_pub=node.create_publisher(NavPath,"/axia/d08/official_path_readonly",
        QoSProfile(depth=1,reliability=ReliabilityPolicy.RELIABLE,
                   durability=DurabilityPolicy.TRANSIENT_LOCAL))
    exe=SingleThreadedExecutor()
    exe.add_node(node)
    thread=None
    moved=False
    operation_spans=[]
    process_heartbeat_samples=deque(maxlen=2048)
    process_heartbeat_stop=threading.Event()

    def heartbeat_process_loop():
        # CI-only low-overhead 20ms witness; detects whether ALL Python
        # threads pause or only ROS executor callbacks are delayed.
        while not process_heartbeat_stop.is_set():
            process_heartbeat_samples.append({
                "host_monotonic_sec":time.monotonic(),
                "process_cpu_sec":time.process_time(),
            })
            process_heartbeat_stop.wait(.02)

    process_heartbeat_thread=threading.Thread(
        target=heartbeat_process_loop,daemon=True)

    def record_span(name,start):
        # Bounded diagnostic of exact host-monotonic synchronous operations.
        if len(operation_spans)<48:
            operation_spans.append({
                "name":name,
                "start_sec":round(start,6),
                "end_sec":round(time.monotonic(),6),
            })

    def on_scan(msg):
        entry_at=time.monotonic()  # callback entry, before per-range CPU work
        if _stamp(msg)<=0:return
        bearing=math.atan2(CANDIDATE_MAP[1]-START_MAP[1],
                           CANDIDATE_MAP[0]-START_MAP[0])
        valid=[float(d) for i,d in enumerate(msg.ranges)
               if math.isfinite(float(d)) and d>0
               and abs(math.atan2(math.sin(msg.angle_min+i*msg.angle_increment-bearing),
                                  math.cos(msg.angle_min+i*msg.angle_increment-bearing)))<.09]
        with callbacks_lock:
            scan_rows.append({"at":time.monotonic(),"entry_at":entry_at,
                  "stamp":_stamp(msg),
                 "sector_min_m":min(valid) if valid else None,
                 "frame":msg.header.frame_id})

    def on_grid(msg):
        if _stamp(msg)<=0:return
        try: count=_lethal_near(msg)
        except (ValueError,IndexError):return
        with callbacks_lock:
            costmap_rows.append({"at":time.monotonic(),"stamp":_stamp(msg),
                                 "lethal_near":count,"frame":msg.header.frame_id})

    def on_odom(msg):
        if _stamp(msg)<=0:return
        with callbacks_lock:
            odom_rows.append({"at":time.monotonic(),"stamp":_stamp(msg),
                "linear":float(msg.twist.twist.linear.x),
                "angular":float(msg.twist.twist.angular.z),
                "xy":[float(msg.pose.pose.position.x),float(msg.pose.pose.position.y)]})

    subs=[
        node.create_subscription(LaserScan,"/scan",on_scan,qos_profile_sensor_data),
        node.create_subscription(OccupancyGrid,"/global_costmap/costmap",on_grid,
            QoSProfile(depth=4,reliability=ReliabilityPolicy.RELIABLE,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL)),
        node.create_subscription(Odometry,"/odom",on_odom,qos_profile_sensor_data),
    ]
    action=ActionClient(node,ComputePathToPose,"/compute_path_to_pose")
    tfbuf=Buffer()
    listener=TransformListener(tfbuf,node,spin_thread=False)
    thread=threading.Thread(target=exe.spin,daemon=True)

    # Read-only, independent ROS callback witness. Different executor thread
    # still shares the host/GIL, so it cannot prove native publisher/RMW gaps.
    independent_node=Node("axia_d08_independent_rx_no_goal")
    independent_executor=SingleThreadedExecutor()
    independent_executor.add_node(independent_node)
    independent_lock=threading.Lock()
    independent_events=new_independent_rx_buffers()

    def independent_cb(topic,msg):
        received=time.monotonic()
        try:
            stamp=(msg.clock if topic=="clock" else
                   msg.transforms[-1].header.stamp if topic=="tf" and msg.transforms
                   else msg.header.stamp)
            source_ns=int(stamp.sec)*1_000_000_000+int(stamp.nanosec)
        except (AttributeError,IndexError):
            source_ns=None
        with independent_lock:
            independent_events[topic].append(
                {"at":received,"stamp_ns":source_ns})

    independent_subs=[
        independent_node.create_subscription(
            LaserScan,"/scan",lambda m:independent_cb("scan",m),
            qos_profile_sensor_data),
        independent_node.create_subscription(
            Odometry,"/odom",lambda m:independent_cb("odom",m),
            qos_profile_sensor_data),
        independent_node.create_subscription(
            Clock,"/clock",lambda m:independent_cb("clock",m),
            qos_profile_sensor_data),
        independent_node.create_subscription(
            TFMessage,"/tf",lambda m:independent_cb("tf",m),
            qos_profile_sensor_data),
    ]
    independent_thread=threading.Thread(
        target=independent_executor.spin,daemon=True)

    def independent_snapshot():
        with independent_lock:
            return {k:list(v) for k,v in independent_events.items()}

    def snapshot():
        with callbacks_lock:
            return list(scan_rows),list(costmap_rows),list(odom_rows)

    def until(predicate,code,seconds=timeout_s):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            item=predicate()
            if item is not None and item is not False:
                return item
            time.sleep(.12)
        raise RuntimeError("D08_"+code+"_FIRST_REAL_BOUNDARY")

    def read_official_cm_native_state_and_scan():
        # A DDS node name can be '_NODE_NAME_UNKNOWN_' even while the
        # official collision_monitor is active. Query its own services
        # instead of assuming which anonymous endpoint subscribed.
        state_cli=node.create_client(GetState,"/collision_monitor/get_state")
        param_cli=node.create_client(
            GetParameters,"/collision_monitor/get_parameters")
        started=time.monotonic()
        state_ready=state_cli.wait_for_service(timeout_sec=8)
        record_span("cm_get_state_service_wait",started)
        if not state_ready:
            raise RuntimeError("D08_OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED:GET_STATE_ABSENT")
        started=time.monotonic()
        params_ready=param_cli.wait_for_service(timeout_sec=8)
        record_span("cm_get_parameters_service_wait",started)
        if not params_ready:
            raise RuntimeError("D08_OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED:GET_PARAMETERS_ABSENT")
        # Native lifecycle service can exist while activation is still
        # transitioning. Read ONLY real service responses until ACTIVE,
        # bounded to 12 seconds; inactive/finalized never yields a PASS.
        state_deadline=time.monotonic()+12.0
        state=None
        states_seen=[]
        while time.monotonic()<state_deadline:
            state_future=state_cli.call_async(GetState.Request())
            until(lambda:state_future.done(),
                  "OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED:STATE_REPLY_TIMEOUT",4)
            state=state_future.result()
            if state is None:
                raise RuntimeError("D08_OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED:EMPTY_STATE")
            observed=(int(state.current_state.id),str(state.current_state.label))
            states_seen.append(observed)
            if cm_state_is_active(*observed):
                break
            time.sleep(.2)
        if state is None or not cm_state_is_active(
                int(state.current_state.id),str(state.current_state.label)):
            raise RuntimeError("D08_OFFICIAL_CM_ACTIVATION_NOT_READY:"+str(states_seen[-5:]))
        req=GetParameters.Request()
        req.names=["observation_sources","scan.topic"]
        param_future=param_cli.call_async(req)
        until(lambda:param_future.done(),
              "OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED:PARAM_REPLY_TIMEOUT",8)
        params=param_future.result()
        if params is None or len(params.values)!=2:
            raise RuntimeError("D08_OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED:PARAM_VALUES_ABSENT")
        sources=list(params.values[0].string_array_value)
        topic=str(params.values[1].string_value)
        try:
            witness=assess_official_cm_native_scan(
                int(state.current_state.id),str(state.current_state.label),
                sources,topic)
        except ValueError as exc:
            raise RuntimeError(
                "D08_OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED:"+str(exc)) from exc
        witness["cm_native_state_observed_transitions"]=[list(x) for x in states_seen]
        witness["cm_native_state_service"]="/collision_monitor/get_state"
        witness["cm_native_param_service"]="/collision_monitor/get_parameters"
        witness["cm_native_observation_sources"]=sources
        witness["cm_native_verified_at_monotonic_s"]=round(time.monotonic(),6)
        return witness

    def move(stage, xyz):
        request=('name: "axia_p2_g07_obstacle", '
            'position: {x: %.9f, y: %.9f, z: %.4f}, orientation: {w: 1}'%
            (xyz[0],xyz[1],xyz[2]))
        pose_start=time.monotonic()
        cp=subprocess.run(['gz','service','-s','/world/default/set_pose',
              '--reqtype','gz.msgs.Pose','--reptype','gz.msgs.Boolean',
              '--timeout','5000','--req',request],
              env=env,text=True,capture_output=True,timeout=13,check=False)
        record_span("gazebo_native_set_pose",pose_start)
        (out/f'{stage}_native_ack.txt').write_text(cp.stdout+cp.stderr)
        if cp.returncode!=0 or "data: true" not in cp.stdout:
            raise RuntimeError("D08_"+stage.upper()+"_NATIVE_SET_POSE_NOT_ACKNOWLEDGED")
        return time.monotonic()

    def stage_observed(t_move,expected):
        def pred():
            scans,grids,odoms=snapshot()
            s=next((x for x in reversed(scans) if x["at"]>t_move and x["sector_min_m"] is not None),None)
            g=next((x for x in reversed(grids) if x["at"]>t_move),None)
            o=odoms[-1] if odoms else None
            if not s or not g or not o:return None
            if not(abs(o["linear"])<.01 and abs(o["angular"])<.02):
                raise RuntimeError("D08_STATIONARY_WAFFLE_ODOM_VIOLATED")
            if expected=="near" and (s["sector_min_m"] is None or s["sector_min_m"]>.90):
                return None
            if expected=="far" and s["sector_min_m"] is not None and s["sector_min_m"]<.8:
                return None
            return s,g,o
        return until(pred,expected.upper()+"_REAL_SCAN_COSTMAP_NOT_UPDATED")

    def compute():
        if not action.wait_for_server(timeout_sec=8):
            raise RuntimeError("D08_OFFICIAL_NAV2_PLANNER_ACTION_ABSENT")
        def get_tf():
            try:
                return tfbuf.lookup_transform("map","base_link",Time())
            except TransformException:return None
        tf=until(get_tf,"REAL_MAP_BASE_LINK_TF_ABSENT",8)
        goal=ComputePathToPose.Goal()
        def pose(x,y):
            p=PoseStamped()
            p.header.frame_id="map"
            p.header.stamp=node.get_clock().now().to_msg()
            p.pose.position.x=float(x)
            p.pose.position.y=float(y)
            p.pose.orientation.w=1.
            return p
        goal.start=pose(tf.transform.translation.x,tf.transform.translation.y)
        goal.goal=pose(*GOAL_MAP)
        goal.use_start=True
        goal.planner_id="GridBased"
        future=action.send_goal_async(goal)
        until(lambda:future.done(),"NAV2_ACTION_REQUEST_TIMEOUT",12)
        h=future.result()
        if not h or not h.accepted:
            raise RuntimeError("D08_OFFICIAL_PATH_ACTION_REJECTED")
        result_future=h.get_result_async()
        until(lambda:result_future.done(),"NAV2_ACTION_RESULT_TIMEOUT",18)
        response=result_future.result()
        if response is None or response.status!=GoalStatus.STATUS_SUCCEEDED:
            raise RuntimeError("D08_OFFICIAL_PATH_ABORTED_STATUS_"+
                               str(response.status if response is not None else "NULL"))
        path=response.result.path
        if path.header.frame_id!="map" or len(path.poses)<3 or _stamp(path)<=0:
            raise RuntimeError("D08_OFFICIAL_PATH_FRAME_STAMP_OR_LENGTH_INVALID")
        pts=[[float(p.pose.position.x),float(p.pose.position.y)] for p in path.poses]
        path_pub.publish(path)  # actual result.result.path, unchanged source stamps
        result["readonly_rviz_path_topic"]="/axia/d08/official_path_readonly"
        return {"poses":pts,"path_stamp":_stamp(path),
                "path_distance_from_obstacle_m":round(_path_distance_to_point(pts,CANDIDATE_MAP),6)}

    native_trace=out/"native_gz_scan_rx.jsonl"
    native_clock_trace=out/"native_gz_clock_rx.jsonl"
    native_enabled=env.get("AXIA_D08_NATIVE_RX_PROBE")=="1"
    native_proc=None
    native_log=None
    isolated_trace=out/"isolated_ros_scan_rx.jsonl"
    isolated_enabled=env.get("AXIA_D08_ROS_ISOLATED_RX_PROBE")=="1"
    isolated_proc=None
    isolated_log=None

    try:
        # ARM both independent receive processes before the original ROS
        # executor can record its FIRST callback. A previous real 515.572ms
        # gap occurred before the native or isolated process subscribed.
        if native_enabled:
            # CI-only, separate-process Gazebo Transport Rx; no publisher.
            native_log=(out/"native_gz_scan_rx.log").open("w")
            native_proc=subprocess.Popen([
                "/usr/bin/python3", "-u",
                str(Path(__file__).with_name("d08_gz_native_scan_probe.py")),
                "--topic", "/scan",
                "--out", str(native_trace),
                "--clock-out", str(native_clock_trace),
                "--max-events", "1024",
                "--max-clock-events", "2048",
            ],env=env,stdin=subprocess.DEVNULL,stdout=native_log,
              stderr=subprocess.STDOUT)
            def native_has_samples():
                if native_proc.poll() is not None:
                    raise RuntimeError("D08_NATIVE_GZ_SCAN_PROBE_EARLY_EXIT")
                return native_trace.exists() and native_trace.stat().st_size>0
            until(native_has_samples,"NATIVE_GZ_SCAN_RX_NOT_READY",9)
        if isolated_enabled:
            isolated_log=(out/"isolated_ros_scan_rx.log").open("w")
            isolated_proc=subprocess.Popen([
                "/usr/bin/python3","-u",
                str(Path(__file__).with_name("d08_ros_isolated_scan_probe.py")),
                "--out",str(isolated_trace),"--max-samples","1024",
            ],env=env,stdin=subprocess.DEVNULL,stdout=isolated_log,
              stderr=subprocess.STDOUT)
            def isolated_has_samples():
                if isolated_proc.poll() is not None:
                    raise RuntimeError("D08_ISOLATED_ROS_SCAN_PROBE_EARLY_EXIT")
                return isolated_trace.exists() and isolated_trace.stat().st_size>0
            until(isolated_has_samples,"ISOLATED_ROS_SCAN_RX_NOT_READY",9)
        result["probe_armed_at_host_monotonic_sec"]=round(time.monotonic(),6)
        result["first_gap_probes_armed_before_observer"]=True
        if isolated_enabled:
            process_heartbeat_thread.start()
        thread.start()
        independent_thread.start()
        result["observer_executor_started_at_monotonic_sec"]=round(time.monotonic(),6)
        until(lambda:bool(snapshot()[0] and snapshot()[1] and snapshot()[2]),
              "SCAN_COSTMAP_ODOM_MISSING",25)
        # This information is discovery only: it does not prove a CM callback period.
        graph_start=time.monotonic()
        pubs=node.get_publishers_info_by_topic("/scan")
        record_span("graph_publishers",graph_start)
        graph_start=time.monotonic()
        consumers=node.get_subscriptions_info_by_topic("/scan")
        record_span("graph_subscriptions",graph_start)
        result["real_scan_publishers"]=[{"node":p.node_name,"type":p.topic_type}
                                        for p in pubs]
        result["real_scan_consumers"]=[{"node":p.node_name,"type":p.topic_type}
                                       for p in consumers]
        result["official_cm_scan_subscription_discovered"]=any(
           "collision_monitor" in p.node_name for p in consumers)
        result["native_cm_scan_receive_gap_verified"]=False
        result["safety_cm_state_verified"]=False
        result["scan_graph_anonymous_subscriber_count"]=sum(
            p.node_name=="_NODE_NAME_UNKNOWN_" for p in consumers)
        if not pubs:raise RuntimeError("D08_REAL_SCAN_PUBLISHER_ABSENT")
        cm_probe_start=time.monotonic()
        result.update(read_official_cm_native_state_and_scan())
        record_span("cm_native_service_probe",cm_probe_start)
        print("D08_OFFICIAL_CM_NATIVE_ACTIVE_SCAN_SOURCE_NO_GOAL "+
              json.dumps({k:result.get(k) for k in (
                "official_cm_active_scan_configured",
                "cm_native_lifecycle_state",
                "cm_native_observation_sources",
                "cm_actual_configured_scan_topic",
                "native_cm_scan_receive_gap_verified",
                "safety_cm_state_verified")},sort_keys=True),flush=True)
        for stage,xyz,expect in [
            ("before",FAR_WORLD,"far"),
            ("intrusion",NEAR_WORLD,"near"),
            ("restored",FAR_WORLD,"far")]:
            epoch=move(stage,xyz)
            moved=(stage!="restored")
            s,g,o=stage_observed(epoch,expect)
            if stage=="before":
                until(lambda: next((x for x in reversed(snapshot()[1])
                      if x["at"]>epoch and x["lethal_near"]==0),None),
                      "BASELINE_GLOBAL_COSTMAP_NOT_CLEAR")
            elif stage=="intrusion":
                until(lambda:next((x for x in reversed(snapshot()[1])
                      if x["at"]>epoch and x["lethal_near"]>=3),None),
                      "GLOBAL_COSTMAP_OBSTACLE_MARK_NOT_PROVEN")
            elif stage=="restored":
                until(lambda:next((x for x in reversed(snapshot()[1])
                      if x["at"]>epoch and x["lethal_near"]==0),None),
                      "GLOBAL_COSTMAP_OBSTACLE_RESTORE_NOT_PROVEN")
            s,g,o=stage_observed(epoch,expect)
            p=compute()
            entry={"source":"official_compute_path_to_pose",
                  "stage":stage,"goal_sent":False,"frame":"map",
                  "gazebo_native_ack":True,
                  "native_physical_world_xyz":list(xyz),
                  "scan_stamp":s["stamp"],"costmap_stamp":g["stamp"],
                  "scan_sector_min_m":s["sector_min_m"],
                  "lethal_near":g["lethal_near"],
                  "odom_stamp":o["stamp"],"odom_xy":o["xy"],**p}
            rows.append(entry)
            with (out/"path_phases.jsonl").open("a") as fh:
                fh.write(json.dumps(entry,sort_keys=True)+"\n")
            print("D08_OFFICIAL_REAL_PATH_PHASE "+json.dumps(
                  {k:entry[k] for k in ("stage","path_stamp",
                    "scan_stamp","costmap_stamp","lethal_near",
                    "scan_sector_min_m","path_distance_from_obstacle_m")}),
                  flush=True)
        scans,grids,odoms=snapshot()
        gaps=[b["at"]-a["at"] for a,b in zip(scans,scans[1:])]
        result["scan_sample_count"]=len(scans)
        result["first_scan_receive_gaps_sec"]=[round(v,6) for v in gaps[:12]]
        result["first_scan_wall_gap_over_500ms"]=next((
            {"index":i+1,"gap_sec":round(v,6)}
            for i,v in enumerate(gaps) if v>.5),None)
        # Preserve source-vs-host timing at the FIRST >500ms receive
        # violation. Publisher-vs-bridge causality remains unmeasured.
        result["first_scan_timing_boundary"]=first_scan_receive_gap(
            [(sample["at"],int(round(sample["stamp"]*1e9))) for sample in scans],
            limit_s=.5)
        independent=independent_snapshot()
        first=result["first_scan_timing_boundary"]
        entry_pair=None
        if first:
            i=first["sample_index"]
            entry_pair={"previous_entry_sec":scans[i-1]["entry_at"],
                        "current_entry_sec":scans[i]["entry_at"]}
        candidate=diagnose_first_receive_boundary(
            first, {k:[x["at"] for x in samples]
                    for k,samples in independent.items()},
            observer_first_callback=entry_pair)
        result["first_scan_causality"]=candidate
        result["independent_ros_rx_timing"]={}
        for topic,events in independent.items():
            host_gaps=[b["at"]-a["at"] for a,b in zip(events,events[1:])]
            report={"callback_count":len(events),
                    "max_host_receive_gap_sec":round(max(host_gaps),6)
                    if host_gaps else None,
                    "history_complete":len(events)<INDEPENDENT_RX_HISTORY_LIMIT,
                    "publisher_rmw_gap_measured":False}
            if first:
                start=first["previous_host_monotonic_sec"]-.15
                end=first["current_host_monotonic_sec"]+.15
                report["near_first_boundary"]=[
                    {"at":round(x["at"],6),"stamp_ns":x["stamp_ns"]}
                    for x in events if start<=x["at"]<=end][:32]
            result["independent_ros_rx_timing"][topic]=report
        result["scan_observer_callback_processing_max_sec"]=round(
            max((x["at"]-x["entry_at"]) for x in scans),6) if scans else None
        result["scan_observer_first_gap_entry_pair"]=entry_pair
        result["same_monotonic_clock_domain"]=True
        result["native_gazebo_scan_publisher_cadence_measured"]=False
        result["bridge_dds_send_cadence_measured"]=False
        result["three_phases"]=rows
        result.update(evaluate_three_phases(rows,gaps))
    except Exception as exc:
        result["first_boundary"]=type(exc).__name__+":"+str(exc)[:250]
        print("D08_REAL_THREE_PATHS_HOLD "+result["first_boundary"],flush=True)
    finally:
        if process_heartbeat_thread.ident is not None:
            process_heartbeat_stop.set()
            process_heartbeat_thread.join(timeout=1)
        if moved:
            try:
                move("cleanup_restore",FAR_WORLD)
                result["cleanup_restored_far"]=True
            except Exception as exc:
                result["cleanup_error"]=str(exc)[:180]
        result.setdefault("three_phases",rows)
        if native_proc is not None:
            native_proc.terminate()
            try:
                native_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                native_proc.kill()
                native_proc.wait(timeout=2)
        if native_log is not None:
            native_log.close()
        if isolated_proc is not None:
            isolated_proc.terminate()
            try:
                isolated_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                isolated_proc.kill()
                isolated_proc.wait(timeout=2)
        if isolated_log is not None:
            isolated_log.close()
        if native_enabled:
            events=[]
            try:
                if native_trace.is_file():
                    events=[json.loads(line) for line in native_trace.read_text().splitlines()
                            if line.strip()]
            except (OSError, ValueError) as exc:
                result["native_scan_read_error"]=str(exc)[:200]
            clock_events=[]
            try:
                if native_clock_trace.is_file():
                    clock_events=[
                        json.loads(line) for line in
                        native_clock_trace.read_text().splitlines()
                        if line.strip()]
            except (OSError,ValueError) as exc:
                result["native_clock_read_error"]=str(exc)[:200]
            stamps=[x.get("source_stamp_ns") for x in events]
            gaps=[b["host_monotonic_sec"]-a["host_monotonic_sec"]
                  for a,b in zip(events,events[1:])]
            first=result.get("first_scan_timing_boundary")
            result["native_scan_transport_rx"]={
                "enabled":True,
                "sample_count":len(events),
                "source_stamp_ns_count":len(set(stamps)),
                "max_host_receive_gap_sec":round(max(gaps),6) if gaps else None,
                "history_complete":len(events)<1024,
                "source":"gz.transport13 native LaserScan subscriber",
                "publisher_send_timing_proven":False,
                "bridge_dds_send_measured":False,
                "first_violation_cause":"UNDETERMINED",
                "first_gap_crosscheck":compare_native_scan_first_gap(first,events),
                "clock_sample_count":len(clock_events),
                "clock_history_complete":len(clock_events)<2048,
                "clock_max_host_receive_gap_sec":round(
                    max((b["host_monotonic_sec"]-a["host_monotonic_sec"])
                        for a,b in zip(clock_events,clock_events[1:])),6)
                    if len(clock_events)>1 else None,
                "first_gap_clock_layer":diagnose_native_clock_during_first_gap(
                    first,events,clock_events),
            }
            if (len(events)<8 or len(set(stamps))<8 or len(events)>=1024
                    or len(clock_events)<8 or len(clock_events)>=2048):
                result["status"]="HOLD"
                result.setdefault("first_boundary","D08_NATIVE_GZ_SCAN_RX_EVIDENCE_INCOMPLETE")
            print("D08_NATIVE_GZ_SCAN_RX_WITNESS "
                  +json.dumps({k:result["native_scan_transport_rx"][k] for k in
                       ("sample_count","max_host_receive_gap_sec",
                        "history_complete","clock_sample_count",
                        "clock_max_host_receive_gap_sec",
                        "first_violation_cause")}),
                  flush=True)
        if isolated_enabled:
            iso_events=[]
            native_events=[]
            try:
                if isolated_trace.is_file():
                    iso_events=[json.loads(line) for line in
                                isolated_trace.read_text().splitlines() if line.strip()]
                if native_trace.is_file():
                    native_events=[json.loads(line) for line in
                                   native_trace.read_text().splitlines() if line.strip()]
            except (OSError,ValueError) as exc:
                result["isolated_ros_scan_read_error"]=str(exc)[:200]
            iso_gaps=[b["host_monotonic_sec"]-a["host_monotonic_sec"]
                      for a,b in zip(iso_events,iso_events[1:])]
            result["isolated_ros_process_scan_rx"]={
                "enabled":True,
                "separate_process":True,
                "sample_count":len(iso_events),
                "history_complete":len(iso_events)<1024,
                "max_host_receive_gap_sec":round(max(iso_gaps),6)
                    if iso_gaps else None,
                "first_gap_crosscheck":compare_isolated_ros_first_gap(
                    result.get("first_scan_timing_boundary"),
                    iso_events,native_events),
                "bridge_dds_internal_send_measured":False,
                "root_resource_cause":"UNDETERMINED",
            }
            # Compare the WORST original Scan callback gap whose exact two
            # source stamps were seen at all three receiver layers. Even a
            # 493ms near-boundary matters; this is diagnosis, NOT a 500ms
            # safety violation unless the original gap exceeded the limit.
            original_scans=snapshot()[0]
            same_ros=independent_snapshot()["scan"]
            same_rows=[
                {"source_stamp_ns":x["stamp_ns"],
                 "host_monotonic_sec":x["at"]}
                for x in same_ros if x["stamp_ns"] is not None]
            stamp_sets=[
                {x["source_stamp_ns"] for x in rows}
                for rows in (native_events,iso_events,same_rows)]
            available=set.intersection(*stamp_sets) if stamp_sets else set()
            pairs=[]
            for before,after in zip(original_scans,original_scans[1:]):
                n1=int(round(before["stamp"]*1e9))
                n2=int(round(after["stamp"]*1e9))
                if n1 in available and n2 in available:
                    pairs.append((after["at"]-before["at"],before,after,n1,n2))
            if pairs:
                biggest,before,after,n1,n2=max(pairs,key=lambda x:x[0])
                pair={"previous_ros_stamp_ns":n1,
                      "current_ros_stamp_ns":n2,
                      "previous_host_monotonic_sec":round(before["at"],6),
                      "current_host_monotonic_sec":round(after["at"],6),
                      "receive_gap_sec":round(biggest,6)}
                cmp=compare_worst_scan_pair_receivers(
                    pair,native_events,iso_events,same_rows)
                cmp["parent_callback_entry_gap_sec"]=round(
                    after["entry_at"]-before["entry_at"],6)
                cmp["operation_overlap_report"]=scan_gap_operation_overlaps(
                    pair,operation_spans)
                cmp["process_heartbeat"]=analyze_process_heartbeat_gap(
                    pair,list(process_heartbeat_samples))
                result["worst_scan_causal_pair"]=cmp
                result["worst_scan_pair_source_stamps"]=pair
                print("D08_REAL_WORST_SCAN_SOURCE_PAIR "
                      +json.dumps({k:cmp[k] for k in
                        ("observer_gap_sec","native_gap_sec",
                         "isolated_ros_gap_sec","same_python_gap_sec",
                         "candidate","source_pair_matched")},sort_keys=True),
                      flush=True)
            else:
                result["worst_scan_causal_pair"]={
                    "cause":"UNDETERMINED",
                    "candidate":"NO_COMMON_SOURCE_PAIR",
                    "source_pair_matched":False}
                result["status"]="HOLD"
                result.setdefault("first_boundary",
                    "D08_NO_MATCHED_SCAN_SOURCE_PAIR_ACROSS_RECEIVERS")
            if len(iso_events)<8 or len(iso_events)>=1024:
                result["status"]="HOLD"
                result.setdefault("first_boundary","D08_ISOLATED_ROS_RX_EVIDENCE_INCOMPLETE")
            print("D08_ISOLATED_ROS_SCAN_PROCESS_WITNESS "+json.dumps({
                k:result["isolated_ros_process_scan_rx"][k] for k in
                ("sample_count","max_host_receive_gap_sec","history_complete")
            },sort_keys=True),flush=True)
        result["process_heartbeat_summary"]={
            "enabled":bool(isolated_enabled),
            "sample_count":len(process_heartbeat_samples),
            "history_complete":len(process_heartbeat_samples)<2048,
            "source":"same_python_process_monotonic_and_process_time",
        }
        if isolated_enabled and (
                len(process_heartbeat_samples)<20 or
                len(process_heartbeat_samples)>=2048):
            result["status"]="HOLD"
            result.setdefault("first_boundary",
                              "D08_PROCESS_HEARTBEAT_EVIDENCE_INCOMPLETE")
        result["read_only_operation_spans"]=operation_spans[:48]
        # No synthetic /scan or arbitrary ROS cmd_vel publisher is created here.
        (out/"verdict.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        independent_executor.shutdown(timeout_sec=2)
        independent_node.destroy_node()
        if independent_thread.ident is not None:
            independent_thread.join(timeout=2)
        exe.shutdown(timeout_sec=3)
        node.destroy_node()
        rclpy.shutdown()
        if thread.ident is not None:thread.join(timeout=2)
    return 0 if result["status"].endswith("_PASS_NO_GOAL") else 2
