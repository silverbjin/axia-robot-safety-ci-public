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

def assess_planner_lifecycle_observation(states):
    """Real GetState ACTIVE is required; Action server discovery is insufficient."""
    if not states or states[-1] != 'active':
        raise RuntimeError('D08_PLANNER_LIFECYCLE_NOT_ACTIVE')
    return {'official_planner_active':True,'observed_states':list(states),
            'action_server_discovery_is_not_lifecycle_admission':True}


def wait_for_planner_active(node,timeout_s=25.0):
    """Query existing official Planner GetState; bounded, read-only and no Goal."""
    import rclpy
    from lifecycle_msgs.srv import GetState
    states=[]
    started=time.monotonic()
    deadline=started+max(0.0,float(timeout_s))
    cli=node.create_client(GetState,'/planner_server/get_state')
    try:
        while time.monotonic()<deadline:
            if not cli.service_is_ready():
                rclpy.spin_once(node,timeout_sec=.05)
                continue
            future=cli.call_async(GetState.Request())
            remaining=deadline-time.monotonic()
            rclpy.spin_until_future_complete(node,future,timeout_sec=min(2.0,max(.01,remaining)))
            if not future.done() or future.exception() is not None:
                raise RuntimeError('D08_PLANNER_LIFECYCLE_GET_STATE_NO_ACK')
            response=future.result()
            state=str(response.current_state.label)
            if len(states)<30 or state!=states[-1]:
                states.append(state)
            if state=='active':
                result=assess_planner_lifecycle_observation(states)
                result['wait_wall_sec']=round(time.monotonic()-started,6)
                result['native_service']='/planner_server/get_state'
                print('D08_OFFICIAL_PLANNER_LIFECYCLE_ACTIVE_NO_GOAL '+json.dumps(
                    result,sort_keys=True),flush=True)
                return result
            rclpy.spin_once(node,timeout_sec=.1)
        raise RuntimeError('D08_PLANNER_LIFECYCLE_NOT_ACTIVE:'+str(states[-5:]))
    finally:
        node.destroy_client(cli)


def run(out:Path,timeout_s=25,*,initialize_amcl=False,spawn_xy=None):
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
        if initialize_amcl:
            # Public D07-H01 P0 contract: one officially-acknowledged initial
            # map pose, followed by genuine AMCL + map->base_link TF.
            # No synthetic transform / Twist / moving goal.
            if (not isinstance(spawn_xy,(tuple,list)) or len(spawn_xy)!=2
                or any(not math.isfinite(float(v)) for v in spawn_xy)):
                raise ValueError('D08_AMCL_PINNED_SPAWN_REQUIRED')
            from d08_amcl_initial_pose import admit_actual_amcl
            verdict['real_amcl_and_tf']=admit_actual_amcl(
                node,float(spawn_xy[0]),float(spawn_xy[1]),
                timing_out=out.parent/'amcl_receive_timing.json')
            if not verdict['real_amcl_and_tf']['localization_verified']:
                raise RuntimeError('D08_AMCL_INITIAL_POSE_ACK_NOT_LOCALIZATION')
            print('D08_OFFICIAL_AMCL_REAL_TF_READY_NO_GOAL '+json.dumps(
                verdict['real_amcl_and_tf'],sort_keys=True),flush=True)
        verdict['planner_lifecycle']=wait_for_planner_active(node,timeout_s=timeout_s)
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
