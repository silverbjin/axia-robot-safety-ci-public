#!/usr/bin/env python3
"""D08 GUI only: READ-ONLY official Nav2 ComputePathToPose proof before Goal.

Plan through the live costmap in current P2 scene. Does not send NavigateToPose,
publish Twist, alter the official map, inflate/deflate obstacles or override P2.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import time

GOAL_MAP=(-1.6,-0.5)

def assess_path(poses,goal=GOAL_MAP):
    if len(poses)<2:
        raise ValueError('D08_NAV2_PATH_TOO_SHORT')
    pts=[(float(p.pose.position.x),float(p.pose.position.y)) for p in poses]
    if not all(math.isfinite(v) for xy in pts for v in xy):
        raise ValueError('D08_NAV2_PATH_NONFINITE')
    distance=sum(math.hypot(b[0]-a[0],b[1]-a[1])
                 for a,b in zip(pts,pts[1:]))
    if not (.05<=distance<=10):
        raise ValueError('D08_NAV2_PATH_LENGTH_INVALID')
    if math.hypot(pts[-1][0]-goal[0],pts[-1][1]-goal[1])>.15:
        raise ValueError('D08_NAV2_PATH_GOAL_MISMATCH')
    return {'path_points':len(pts),'path_length_m':round(distance,3),
            'start_xy':list(pts[0]),'end_xy':list(pts[-1]),
            'goal_xy':list(goal)}

def run(out:Path,timeout_s=25):
    import rclpy
    from rclpy.action import ActionClient
    from rclpy.parameter import Parameter
    from nav2_msgs.action import ComputePathToPose
    from action_msgs.msg import GoalStatus

    out=Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError('D08_PATH_VERDICT_EXISTS')
    out.parent.mkdir(parents=True,exist_ok=True)
    verdict={'status':'BLOCKED','gate':'D08_LIVE_NAV2_COSTMAP_PLAN_BEFORE_GOAL',
             'planning_action':'/compute_path_to_pose',
             'planner_id':'GridBased',
             'goal_map_xy':list(GOAL_MAP),
             'navigate_goal_sent':False,'control_published':False,
             'safety_certified':False,'collision_free_verified':False}
    rclpy.init()
    node=rclpy.create_node('axia_d08_readonly_nav2_path_preflight',
         parameter_overrides=[Parameter('use_sim_time',value=True)])
    client=ActionClient(node,ComputePathToPose,'/compute_path_to_pose')
    try:
        if not client.wait_for_server(timeout_sec=10):
            raise RuntimeError('D08_OFFICIAL_NAV2_PLANNER_UNAVAILABLE')
        # A fresh simulation-time rclpy node must receive /clock BEFORE
        # timestamping a planner request; stale/zero clock cannot pass.
        clock_deadline=time.monotonic()+6
        while (node.get_clock().now().nanoseconds<=0
               and time.monotonic()<clock_deadline):
            rclpy.spin_once(node,timeout_sec=.15)
        if node.get_clock().now().nanoseconds<=0:
            raise RuntimeError('D08_NAV2_PLANNER_SIM_CLOCK_NOT_READY')
        goal=ComputePathToPose.Goal()
        goal.goal.header.frame_id='map'
        goal.goal.header.stamp=node.get_clock().now().to_msg()
        goal.goal.pose.position.x=GOAL_MAP[0]
        goal.goal.pose.position.y=GOAL_MAP[1]
        goal.goal.pose.orientation.w=1.0
        goal.use_start=False
        goal.planner_id='GridBased'
        accepted=client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node,accepted,timeout_sec=10)
        if not accepted.done() or accepted.exception() is not None:
            raise RuntimeError('D08_PLANNER_GOAL_REQUEST_UNANSWERED')
        handle=accepted.result()
        if not handle.accepted:
            raise RuntimeError('D08_PLANNER_REFUSED_PATH_REQUEST')
        future=handle.get_result_async()
        rclpy.spin_until_future_complete(node,future,timeout_sec=timeout_s)
        if not future.done() or future.exception() is not None:
            raise RuntimeError('D08_PLANNER_PATH_TIMEOUT')
        result=future.result()
        if result.status!=GoalStatus.STATUS_SUCCEEDED:
            raise RuntimeError('D08_PLANNER_NOT_SUCCEEDED_STATUS_'+str(result.status))
        verdict['real_costmap_plan']=assess_path(result.result.path.poses)
        verdict['status']='D08_LIVE_NAV2_PATH_CANDIDATE'
        print('D08_LIVE_NAV2_PATH_CANDIDATE '+json.dumps(
             verdict['real_costmap_plan']),flush=True)
    except Exception as exc:
        verdict['blocker']=type(exc).__name__+':'+str(exc)[:250]
        print('D08_LIVE_NAV2_PATH_BLOCKED '+verdict['blocker'],flush=True)
    finally:
        out.write_text(json.dumps(verdict,indent=2,ensure_ascii=False)+'\n')
        client.destroy()
        node.destroy_node()
        rclpy.shutdown()
    return 0 if verdict['status']=='D08_LIVE_NAV2_PATH_CANDIDATE' else 2

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--timeout-s',type=float,default=25.0)
    a=p.parse_args()
    raise SystemExit(run(a.out,a.timeout_s))

if __name__=='__main__':
    main()
