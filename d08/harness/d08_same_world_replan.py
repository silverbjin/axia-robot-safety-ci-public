#!/usr/bin/env python3
"""Read-only D08 physical-person three-phase official Nav2 Path observation.

ONE already-running real Gazebo+Waffle+AMCL world. No robot Goal, Twist,
fake /scan, fake Costmap, custom Planner or changed safety TTL.
D07-H01 L2 world/map coordinates are *candidates*, not evidence for D08.
"""
from __future__ import annotations

from collections import deque
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


def run(out:Path, env:dict, source_sha:str, timeout_s=35.) -> int:
    import rclpy
    from rclpy.action import ActionClient
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from rclpy.qos import (qos_profile_sensor_data, QoSProfile,
                            ReliabilityPolicy, DurabilityPolicy)
    from rclpy.time import Time
    from nav_msgs.msg import OccupancyGrid, Odometry
    from sensor_msgs.msg import LaserScan
    from nav2_msgs.action import ComputePathToPose
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
    exe=MultiThreadedExecutor(num_threads=2)
    exe.add_node(node)
    thread=None
    moved=False

    def on_scan(msg):
        if _stamp(msg)<=0:return
        bearing=math.atan2(CANDIDATE_MAP[1]-START_MAP[1],
                           CANDIDATE_MAP[0]-START_MAP[0])
        valid=[float(d) for i,d in enumerate(msg.ranges)
               if math.isfinite(float(d)) and d>0
               and abs(math.atan2(math.sin(msg.angle_min+i*msg.angle_increment-bearing),
                                  math.cos(msg.angle_min+i*msg.angle_increment-bearing)))<.09]
        with callbacks_lock:
            scan_rows.append({"at":time.monotonic(),"stamp":_stamp(msg),
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
    thread.start()

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

    def move(stage, xyz):
        request=('name: "axia_p2_g07_obstacle", '
            'position: {x: %.9f, y: %.9f, z: %.4f}, orientation: {w: 1}'%
            (xyz[0],xyz[1],xyz[2]))
        cp=subprocess.run(['gz','service','-s','/world/default/set_pose',
              '--reqtype','gz.msgs.Pose','--reptype','gz.msgs.Boolean',
              '--timeout','5000','--req',request],
              env=env,text=True,capture_output=True,timeout=13,check=False)
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
        return {"poses":pts,"path_stamp":_stamp(path),
                "path_distance_from_obstacle_m":round(_path_distance_to_point(pts,CANDIDATE_MAP),6)}

    try:
        until(lambda:bool(snapshot()[0] and snapshot()[1] and snapshot()[2]),
              "SCAN_COSTMAP_ODOM_MISSING",25)
        # This information is discovery only: it does not prove a CM callback period.
        pubs=node.get_publishers_info_by_topic("/scan")
        consumers=node.get_subscriptions_info_by_topic("/scan")
        result["real_scan_publishers"]=[{"node":p.node_name,"type":p.topic_type}
                                        for p in pubs]
        result["real_scan_consumers"]=[{"node":p.node_name,"type":p.topic_type}
                                       for p in consumers]
        result["official_cm_scan_subscription_discovered"]=any(
           "collision_monitor" in p.node_name for p in consumers)
        result["native_cm_scan_receive_gap_verified"]=False
        result["safety_cm_state_verified"]=False
        if not pubs:raise RuntimeError("D08_REAL_SCAN_PUBLISHER_ABSENT")
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
        result["three_phases"]=rows
        result.update(evaluate_three_phases(rows,gaps))
    except Exception as exc:
        result["first_boundary"]=type(exc).__name__+":"+str(exc)[:250]
        print("D08_REAL_THREE_PATHS_HOLD "+result["first_boundary"],flush=True)
    finally:
        if moved:
            try:
                move("cleanup_restore",FAR_WORLD)
                result["cleanup_restored_far"]=True
            except Exception as exc:
                result["cleanup_error"]=str(exc)[:180]
        result.setdefault("three_phases",rows)
        # No synthetic /scan or arbitrary ROS cmd_vel publisher is created here.
        (out/"verdict.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        exe.shutdown(timeout_sec=3)
        node.destroy_node()
        rclpy.shutdown()
        if thread:thread.join(timeout=2)
    return 0 if result["status"].endswith("_PASS_NO_GOAL") else 2
