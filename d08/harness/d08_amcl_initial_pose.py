#!/usr/bin/env python3
"""D08 official Nav2 AMCL initialpose: reuse public D07-H01 P0 contract.

Only same-world map-checked localization initialization. No cmd_vel,
NavigateToPose, FollowPath or fabricated map→odom TF.
"""
from __future__ import annotations
import hashlib
import math
import time


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


def admit_actual_amcl(node, x: float, y: float, timeout_s=24.0) -> dict:
    """Require actual map, actual scan/odom, AMCL service ACK and map TF."""
    import rclpy
    from rclpy.qos import (
        QoSProfile,DurabilityPolicy,ReliabilityPolicy,qos_profile_sensor_data)
    from rclpy.time import Time
    from nav_msgs.msg import OccupancyGrid,Odometry
    from sensor_msgs.msg import LaserScan
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from nav2_msgs.srv import SetInitialPose
    from tf2_ros import Buffer,TransformListener,TransformException

    latest={}
    def recv(kind,msg):
        latest[kind]=(msg,time.monotonic())
    qos=QoSProfile(depth=1,reliability=ReliabilityPolicy.RELIABLE,
                   durability=DurabilityPolicy.TRANSIENT_LOCAL)
    subs=[
        node.create_subscription(OccupancyGrid,"/map",
             lambda m:recv("map",m),qos),
        node.create_subscription(Odometry,"/odom",
             lambda m:recv("odom",m),qos_profile_sensor_data),
        node.create_subscription(LaserScan,"/scan",
             lambda m:recv("scan",m),qos_profile_sensor_data),
        node.create_subscription(PoseWithCovarianceStamped,"/amcl_pose",
             lambda m:recv("amcl_pose",m),10),
    ]
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
        pending=cli.call_async(req)
        rclpy.spin_until_future_complete(node,pending,timeout_sec=12)
        if (not pending.done() or pending.exception() is not None
            or pending.result() is None):
            raise RuntimeError("D08_AMCL_SET_INITIAL_POSE_NO_ACK")
        verdict["amcl_service_ack"]=True
        verdict["amcl_service"]="/set_initial_pose"
        verdict["localization_verified"]=False
        # An empty service ACK is NOT localization; require genuine /amcl_pose
        # plus a TF2 map→base_link chain. Never publish synthetic TF.
        tfbuf=Buffer()
        listener=TransformListener(tfbuf,node,spin_thread=False)
        end=time.monotonic()+18
        last_error="AMCL_POSE_OR_TF_MISSING"
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.2)
            if "amcl_pose" not in latest:
                continue
            amcl=latest["amcl_pose"][0]
            if amcl.header.frame_id!="map" or amcl.header.stamp.sec<=0:
                last_error="AMCL_POSE_FRAME_OR_STAMP_INVALID"
                continue
            if time.monotonic()-latest["amcl_pose"][1]>1.0:
                last_error="AMCL_POSE_STALE"
                continue
            try:
                tf=tfbuf.lookup_transform("map","base_link",Time())
            except TransformException as ex:
                last_error=str(ex)[:180]
                continue
            if tf.header.frame_id!="map" or tf.child_frame_id!="base_link":
                last_error="MAP_BASE_LINK_CHAIN_WRONG"
                continue
            verdict["localization_verified"]=True
            verdict["amcl_pose_stamp_ns"]=int(amcl.header.stamp.sec)*10**9+int(amcl.header.stamp.nanosec)
            verdict["map_base_link_tf_stamp_ns"]=int(tf.header.stamp.sec)*10**9+int(tf.header.stamp.nanosec)
            verdict["map_base_link_tf_source"]="real_tf2_buffer_lookup"
            return verdict
        raise RuntimeError("D08_AMCL_REAL_MAP_BASE_TF_NOT_READY:"+last_error)
    finally:
        for sub in subs:
            node.destroy_subscription(sub)
