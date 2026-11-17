"""Cycle04: only official CM subscription metadata, read-only NO_GOAL.

Use existing exact Cycle31 topic->rcl handle->rclcpp subscription->callback
resolver. Do not print/export raw handles, PIDs, paths, timestamps or UUIDs.
This cannot establish a callback duration or authorize a moving Goal.
"""
from d06.live.g07_cycle31_cm_topic_callback_identity import (
    resolve_cm_cmdvel_handles,
)
import collections

META={
    "ros2:rcl_subscription_init",
    "ros2:rclcpp_subscription_init",
    "ros2:rclcpp_subscription_callback_added",
}
CM_PROCNAMES={"collision_monitor","collision_monit"}

def _hold(status,**more):
    return dict(schema="axia.g07.cycle04.cm_subscription_metadata_v1",
                status=status,metadata_only=True,goal_sent=False,
                cmd_vel_publisher_created=False,
                cm_callback_duration_proven=False,
                tf_lookup_delay_proven=False,ready_for_moving_goal=False,
                owner_l3_accepted=False,certified_estop=False,
                **more)

def classify(rows):
    if not isinstance(rows,list) or len(rows)>20000:
        return _hold("CM_METADATA_INPUT_UNBOUNDED_OR_INVALID_HOLD")
    owned=set()
    claimed=set()
    count=collections.Counter()
    for row in rows:
        if not isinstance(row,dict):
            return _hold("CM_METADATA_ROW_INVALID_HOLD")
        name=row.get("name")
        if name not in META:
            continue
        count[name]+=1
        if name=="ros2:rcl_subscription_init" and row.get("topic_name")=="/cmd_vel_supervised":
            pid=row.get("vpid")
            if type(pid) is not int or pid<=1:
                return _hold("CM_CMD_TOPIC_OWNER_UNVERIFIED_HOLD")
            claimed.add(pid)
            if row.get("procname") in CM_PROCNAMES:
                owned.add(pid)
    if not claimed or len(owned)!=1 or claimed!=owned:
        return _hold("CM_MULTIPLE_CMD_SUBSCRIPTION_PROCESSES_HOLD"
                     if len(owned)>1 else "CM_CMD_TOPIC_OWNER_UNVERIFIED_HOLD",
                     owned_cm_process_count=len(owned),
                     matching_cmd_topic_process_count=len(claimed))
    pid=next(iter(owned))
    try:
        handles,counts=resolve_cm_cmdvel_handles(rows,cm_pid=pid)
    except ValueError:
        return _hold("CM_TOPIC_CALLBACK_TRACE_CHAIN_AMBIGUOUS_HOLD")
    if len(handles)==0 or counts.get("topic_matched_subscriptions")!=1:
        return _hold("CM_INPUT_CALLBACK_LINK_MISSING_HOLD",
                     linked_cmd_vel_callback_handles=0,
                     owned_cm_process_count=1)
    return _hold("CM_INPUT_CALLBACK_HANDLE_IDENTIFIED_NO_GOAL",
                 owned_cm_process_count=1,
                 linked_cmd_vel_callback_handles=len(handles),
                 owned_cm_subscription_init_count=count["ros2:rcl_subscription_init"],
                 rclcpp_subscription_link_count=count["ros2:rclcpp_subscription_init"],
                 callback_added_event_count=count["ros2:rclcpp_subscription_callback_added"])
