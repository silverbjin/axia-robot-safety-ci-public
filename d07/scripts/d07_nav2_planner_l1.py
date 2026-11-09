#!/usr/bin/env python3
"""D07 actual official Nav2 Jazzy planner + costmap dynamic-obstacle ROS L1 gate.

Synthetic person-proxy LaserScan -> official ObstacleLayer/InflationLayer ->
official NavfnPlanner ComputePathToPose. No movement, NavigateToPose, /cmd_vel,
Gazebo, or claim of collision-free robot operation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def _scan(now, *, obstacle):
    from sensor_msgs.msg import LaserScan
    m=LaserScan()
    m.header.stamp=now
    m.header.frame_id="base_footprint"
    m.angle_min=-math.pi
    m.angle_increment=2*math.pi/360
    m.angle_max=m.angle_min + 359*m.angle_increment
    m.scan_time=0.10
    m.range_min=0.05
    m.range_max=8.0
    m.ranges=[7.0]*360
    if obstacle:
        for i in range(360):
            a=m.angle_min+i*m.angle_increment
            if abs(a)<=0.18:
                m.ranges[i]=0.8
    return m


def _pose(node, x, y):
    from geometry_msgs.msg import PoseStamped
    p=PoseStamped()
    p.header.frame_id="map"
    p.header.stamp=node.get_clock().now().to_msg()
    p.pose.position.x=float(x)
    p.pose.position.y=float(y)
    p.pose.orientation.w=1.0
    return p


def _path_min_distance(points, x, y):
    if len(points)<2:
        return float("inf")
    values=[]
    for a,b in zip(points,points[1:]):
        vx=b[0]-a[0];vy=b[1]-a[1]
        m=vx*vx+vy*vy
        t=0 if m<=0 else max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/m))
        values.append(math.hypot(x-a[0]-t*vx,y-a[1]-t*vy))
    return min(values)


def _lethal_near(grid,x,y,radius=0.32):
    if grid is None:
        return 0
    info=grid.info
    if info.resolution<=0 or info.width<2 or info.height<2:
        raise AssertionError("Invalid Nav2 OccupancyGrid resolution")
    ox=info.origin.position.x;oy=info.origin.position.y
    cells=[]
    for iy in range(info.height):
        cy=oy+(iy+0.5)*info.resolution
        if abs(cy-y)>radius:continue
        for ix in range(info.width):
            cx=ox+(ix+0.5)*info.resolution
            if (cx-x)**2+(cy-y)**2>radius*radius:continue
            cell=int(grid.data[iy*info.width+ix])
            if cell>=95:cells.append((round(cx,3),round(cy,3),cell))
    return len(cells)


def _run_stage(node, pub, collected, *, obstacle, duration=3.6):
    import rclpy
    start=time.monotonic()
    last_send=0
    n=0
    while time.monotonic()-start<duration:
        now=time.monotonic()
        if now-last_send>0.10:
            pub.publish(_scan(node.get_clock().now().to_msg(),obstacle=obstacle))
            n+=1;last_send=now
        rclpy.spin_once(node,timeout_sec=0.045)
    grid=collected.get("costmap")
    if n<10 or grid is None or len(grid.data)==0:
        raise RuntimeError(f"No real official Nav2 Costmap after {n} synthetic scans")
    lethal=_lethal_near(grid,0.8,0.0)
    return {
        "scan_count_sent":n,
        "stamp_sec":node.get_clock().now().nanoseconds/1e9,
        "actual_obstacle_lethal_cells":lethal,
        "frame_id":grid.header.frame_id,
        "costmap_width":grid.info.width,
        "costmap_height":grid.info.height,
        "costmap_resolution":grid.info.resolution,
        "costmap_sha256":hashlib.sha256(bytes((int(v)+256)%256 for v in grid.data)).hexdigest(),
    }


def _request_path(node, client):
    import rclpy
    from nav2_msgs.action import ComputePathToPose
    from action_msgs.msg import GoalStatus
    if not client.wait_for_server(timeout_sec=8):
        raise RuntimeError("Official ComputePathToPose action server not ready")
    g=ComputePathToPose.Goal()
    g.start=_pose(node,0.0,0.0)
    g.goal=_pose(node,1.5,0.0)
    g.use_start=True
    g.planner_id="GridBased"
    future=client.send_goal_async(g)
    rclpy.spin_until_future_complete(node,future,timeout_sec=15)
    if not future.done() or future.result() is None:
        raise RuntimeError("ComputePathToPose goal request timeout")
    handle=future.result()
    if not handle.accepted:
        raise RuntimeError("Planner rejected compute-only request")
    result_fut=handle.get_result_async()
    rclpy.spin_until_future_complete(node,result_fut,timeout_sec=16)
    if not result_fut.done() or result_fut.result() is None:
        raise RuntimeError("ComputePathToPose result timeout")
    msg=result_fut.result()
    if msg.status!=GoalStatus.STATUS_SUCCEEDED:
        raise RuntimeError(f"Official Nav2 planner status={msg.status} code={msg.result.error_code} msg={msg.result.error_msg}")
    path=msg.result.path
    poses=[(float(p.pose.position.x),float(p.pose.position.y)) for p in path.poses]
    if len(poses)<2:
        raise AssertionError("No actual route poses")
    return {
        "status":"SUCCEEDED",
        "frame_id":path.header.frame_id,
        "path_point_count":len(poses),
        "start":list(poses[0]),
        "goal":list(poses[-1]),
        "min_distance_to_person_proxy_m":_path_min_distance(poses,0.8,0.0),
        "max_abs_y_m":max(abs(y) for _,y in poses),
        "path_sha256":hashlib.sha256(json.dumps(poses).encode()).hexdigest(),
        "path_xy_sample":poses[::max(1,len(poses)//80)][:90],
    }


def _lifecycle(env,proc,action):
    error=""
    for _ in range(22):
        if proc.poll() is not None:
            raise RuntimeError(f"Official Nav2 planner exited rc={proc.returncode}")
        try:
            p=subprocess.run(["ros2","lifecycle","set","/planner_server",action],
                             env=env,capture_output=True,text=True,timeout=7)
            error=(p.stdout+p.stderr)[-400:]
            if p.returncode==0 and "success" in p.stdout.lower():
                return
        except subprocess.TimeoutExpired:
            error="lifecycle cli timeout"
        time.sleep(0.45)
    raise RuntimeError("Planner lifecycle "+action+" failed: "+error)


def _start_tf(node):
    from geometry_msgs.msg import TransformStamped
    from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
    tf=StaticTransformBroadcaster(node)
    msg=TransformStamped()
    msg.header.stamp=node.get_clock().now().to_msg()
    msg.header.frame_id="map"
    msg.child_frame_id="base_footprint"
    msg.transform.rotation.w=1.0
    tf.sendTransform(msg)
    return tf


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--params",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    params=a.params.resolve(strict=True)
    verdict={
        "gate":"AXIA-D07-OFFICIAL-NAV2-PLANNER-COSTMAP-L1",
        "status":"BLOCKED","ros_actual":False,"gazebo_actual":False,
        "goal_sent":False,"navigate_to_pose_sent":False,
        "cmd_vel_published":False,"robot_moved":False,
        "certified_estop":False,
        "source_params_sha256":hashlib.sha256(params.read_bytes()).hexdigest(),
        "stages":{}
    }
    env=os.environ.copy()
    env["ROS_DOMAIN_ID"]=str(24+os.getpid()%155)
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"]="LOCALHOST"
    os.environ.update({k:env[k] for k in ("ROS_DOMAIN_ID","ROS_AUTOMATIC_DISCOVERY_RANGE")})
    node=None;proc=None
    try:
        import rclpy
        from rclpy.action import ActionClient
        from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy,qos_profile_sensor_data
        from nav_msgs.msg import OccupancyGrid
        from nav2_msgs.action import ComputePathToPose
        from sensor_msgs.msg import LaserScan
        rclpy.init()
        node=rclpy.create_node("axia_d07_readonly_costmap_planner_verifier")
        tf=_start_tf(node)
        collected={}
        def got_costmap(m):
            collected["costmap"]=m
        sub=node.create_subscription(OccupancyGrid,"/global_costmap/costmap",
            got_costmap,QoSProfile(depth=4,reliability=ReliabilityPolicy.RELIABLE,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL))
        pub=node.create_publisher(LaserScan,"/axia/d07/test/scan",qos_profile_sensor_data)
        client=ActionClient(node,ComputePathToPose,"/compute_path_to_pose")
        log=open(out/"planner_server.log","w",encoding="utf-8")
        try:
            proc=subprocess.Popen(
                ["ros2","run","nav2_planner","planner_server","--ros-args",
                 "--params-file",str(params)],
                env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        finally:
            log.close()
        _lifecycle(env,proc,"configure")
        _lifecycle(env,proc,"activate")
        for _ in range(35):
            rclpy.spin_once(node,timeout_sec=0.15)
            if node.count_subscribers("/axia/d07/test/scan")==1 and node.count_publishers("/global_costmap/costmap")>=1:
                break
        verdict["graph"]={
            "actual_nav2_costmap_publishers":node.count_publishers("/global_costmap/costmap"),
            "actual_nav2_scan_subscribers":node.count_subscribers("/axia/d07/test/scan"),
            "actual_robot_cmd_publishers":node.count_publishers("/cmd_vel")
        }
        if (verdict["graph"]["actual_nav2_costmap_publishers"]<1 or
            verdict["graph"]["actual_nav2_scan_subscribers"]!=1 or
            verdict["graph"]["actual_robot_cmd_publishers"]!=0):
            raise AssertionError("Unsafe or incomplete official Nav2 test graph: "+str(verdict["graph"]))
        for name,obstacle in (("clear_before",False),("person_blocking",True),("person_cleared",False)):
            grid=_run_stage(node,pub,collected,obstacle=obstacle)
            route=_request_path(node,client)
            verdict["stages"][name]={"grid":grid,"route":route}
            print("D07_REAL_NAV2_STAGE "+json.dumps({
                "stage":name,"lethal":grid["actual_obstacle_lethal_cells"],
                "path_points":route["path_point_count"],
                "person_clearance_m":round(route["min_distance_to_person_proxy_m"],3),
                "max_abs_y":round(route["max_abs_y_m"],3)}),flush=True)
        before=verdict["stages"]["clear_before"]
        blocked=verdict["stages"]["person_blocking"]
        cleared=verdict["stages"]["person_cleared"]
        if before["grid"]["actual_obstacle_lethal_cells"]>2:
            raise AssertionError("Unexpected obstacle in baseline official Costmap")
        if blocked["grid"]["actual_obstacle_lethal_cells"]<3:
            raise AssertionError("Actual official ObstacleLayer did not mark person proxy")
        if blocked["route"]["min_distance_to_person_proxy_m"]<0.30:
            raise AssertionError("Real Nav2 planned path overlaps marked person proxy")
        if not (blocked["route"]["max_abs_y_m"] >= before["route"]["max_abs_y_m"] + 0.12):
            raise AssertionError("Nav2 plan did not deviate around obstacle")
        if cleared["grid"]["actual_obstacle_lethal_cells"]>2:
            raise AssertionError("Nav2 obstacle clearing did not remove proxy")
        verdict["status"]="PASS_OFFICIAL_NAV2_COSTMAP_REPLAN_L1"
        verdict["ros_actual"]=True
    except Exception as ex:
        verdict["blocker"]=f"{type(ex).__name__}:{str(ex)[:600]}"
        print("D07_NAV2_L1_BLOCKED "+verdict["blocker"],flush=True)
    finally:
        if node is not None:
            try:node.destroy_node()
            except Exception:pass
            try:
                import rclpy
                if rclpy.ok():rclpy.shutdown()
            except Exception:pass
        if proc is not None:
            if proc.poll() is None:
                try:os.killpg(proc.pid,signal.SIGINT)
                except ProcessLookupError:pass
                try:proc.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=4)
            verdict["official_planner_exit_code"]=proc.returncode
        (out/"verdict.json").write_text(json.dumps(verdict,indent=2,
            ensure_ascii=False,allow_nan=False)+"\n")
        (out/"SHA256SUMS").write_text("".join(
            hashlib.sha256(f.read_bytes()).hexdigest()+"  "+f.name+"\n"
            for f in sorted(out.iterdir()) if f.is_file() and f.name!="SHA256SUMS"))
        print("D07_NAV2_L1_VERDICT "+json.dumps({k:verdict.get(k) for k in
            ("status","ros_actual","gazebo_actual","blocker","graph")}),flush=True)
    return 0 if verdict["status"]=="PASS_OFFICIAL_NAV2_COSTMAP_REPLAN_L1" else 2


if __name__=="__main__":
    raise SystemExit(main())
