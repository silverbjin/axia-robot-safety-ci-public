#!/usr/bin/env python3
"""Jazzy LTTng exact CollisionMonitor velocity subscriber callback identity.

Unlike C++ callback symbols (which can be std::function wrappers), ROS 2
subscription tracepoints expose a verifiable topic->rcl handle->rclcpp
subscription object->callback pointer chain. Only the exact owned CM vpid
is used. Returns handles IN PROCESS MEMORY for the bounded callback oracle,
but prints only sanitized numeric totals; never raw trace, pointers, UUIDs.
No ROS node, Goal, policy change or E-Stop claim.
"""
from __future__ import annotations

TOPIC="/cmd_vel_supervised"
def _pointer(row,key):
    v=row.get(key)
    if type(v) not in (str,int) or str(v)=="":
        raise ValueError("CM_TRACE_SUBSCRIPTION_METADATA_INVALID")
    return str(v)

def resolve_cm_cmdvel_handles(traced,*,cm_pid):
    if not isinstance(traced,list) or type(cm_pid) is not int or cm_pid<=1:
        raise ValueError("CM_TRACE_IDENTITY_INPUT_INVALID")
    topics={}
    subs={}
    callbacks={}
    seen={"rcl":0,"rclcpp":0,"added":0}
    for event in traced:
        if not isinstance(event,dict):
            raise ValueError("CM_TRACE_EVENT_INVALID")
        if event.get("vpid")!=cm_pid:
            continue
        name=event.get("name")
        if name=="ros2:rcl_subscription_init":
            handle=_pointer(event,"subscription_handle")
            topic=event.get("topic_name")
            if type(topic) is not str:
                raise ValueError("CM_TRACE_TOPIC_NAME_MISSING")
            if handle in topics and topics[handle]!=topic:
                raise ValueError("CM_TOPIC_CALLBACK_AMBIGUOUS")
            topics[handle]=topic
            seen["rcl"]+=1
        elif name=="ros2:rclcpp_subscription_init":
            handle=_pointer(event,"subscription_handle")
            sub=_pointer(event,"subscription")
            if sub in subs and subs[sub]!=handle:
                raise ValueError("CM_TOPIC_CALLBACK_AMBIGUOUS")
            subs[sub]=handle
            seen["rclcpp"]+=1
        elif name=="ros2:rclcpp_subscription_callback_added":
            sub=_pointer(event,"subscription")
            callback=_pointer(event,"callback")
            if callback in callbacks and callbacks[callback]!=sub:
                raise ValueError("CM_TOPIC_CALLBACK_AMBIGUOUS")
            callbacks[callback]=sub
            seen["added"]+=1
    target={h for h,topic in topics.items() if topic==TOPIC}
    chain={cb for cb,sub in callbacks.items()
           if sub in subs and subs[sub] in target}
    # A callback object may not identify both CM input and another topic.
    for cb in chain:
        sub=callbacks[cb]
        if not (sub in subs and subs[sub] in target):
            raise ValueError("CM_TOPIC_CALLBACK_AMBIGUOUS")
    counts={
        "schema":"axia.g07.cm_subscription_callback_identity_v1",
        "topic_matched_subscriptions":len(target),
        "rcl_subscription_metadata_seen":seen["rcl"],
        "rclcpp_subscription_metadata_seen":seen["rclcpp"],
        "rclcpp_callback_link_metadata_seen":seen["added"],
        "linked_cmd_vel_callback_handles":len(chain),
        "identity_source":"RCL_SUBSCRIPTION_TOPIC_CALLBACK_CHAIN",
        "raw_trace_exported":False,
        "owner_goal_authorized":False,
        "owner_l3_accepted":False,
        "certified_estop":False,
        "no_ros_no_goal":True,
    }
    return chain,counts
