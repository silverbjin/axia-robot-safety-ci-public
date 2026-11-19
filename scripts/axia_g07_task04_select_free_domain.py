#!/usr/bin/env python3
"""G07 Owner ONLY: detect foreign ROS graph and select an unused DDS domain.

Read-only prelaunch DDS graph: never publishes /clock, Goal or Twist, and never
signals any unrelated ROS/Gazebo process. GZ_PARTITION isolation alone does not
isolate ROS_DOMAIN_ID. A CLI override must be clean or fail closed.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys

def count_clock_backwards(stamps, tolerance_sec=0.001):
    """Real field CDR /clock regression: total backward interarrival pairs."""
    return sum(float(a)-float(b) > tolerance_sec
               for a,b in zip(stamps,stamps[1:]))

def choose_domain(candidates, probe):
    reports=[]
    for domain in candidates:
        try:
            r=probe(domain)
            counts=(r.get("node_count"),r.get("clock_publishers"),
                    r.get("scan_publishers"))
            if not all(type(v) is int and v>=0 for v in counts):
                raise ValueError("INCOMPLETE_DDS_GRAPH_PROBE")
            busy=any(counts)
            reports.append({"domain_id":domain, "status":"BUSY" if busy else "FREE",
                            "node_count":counts[0], "clock_publishers":counts[1],
                            "scan_publishers":counts[2]})
            if not busy:
                return {"schema":"axia.g07.task04.clean_ros_domain_v1",
                        "status":"SELECTED","domain_id":domain,
                        "candidates":reports,"goal_sent":False}
        except Exception as exc:
            reports.append({"domain_id":domain,"status":"PROBE_ERROR",
                            "error_type":type(exc).__name__})
    return {"schema":"axia.g07.task04.clean_ros_domain_v1",
            "status":"NO_FREE_DOMAIN","domain_id":None,
            "candidates":reports,"goal_sent":False}

def probe_rclpy(domain_id):
    # Import only after caller has sourced the official Jazzy environment.
    import rclpy
    ctx=rclpy.context.Context()
    node=None
    try:
        rclpy.init(context=ctx,domain_id=domain_id)
        name="axia_g07_domain_probe_"+str(os.getpid())
        node=rclpy.create_node(name,context=ctx,enable_rosout=False,
                               use_global_arguments=False)
        # Actual DDS endpoint discovery, not cached 'ros2 daemon' results.
        # Bounded at ~1.8s per candidate; CI with an occupied graph must
        # reject the candidate instead of hoping a stale /clock goes away.
        for _ in range(6):
            rclpy.spin_once(node,timeout_sec=.3)
        peers=sum(1 for n,ns in node.get_node_names_and_namespaces()
                  if n!=name or ns!="/")
        return {"node_count":peers,
                "clock_publishers":len(node.get_publishers_info_by_topic("/clock")),
                "scan_publishers":len(node.get_publishers_info_by_topic("/scan"))
                                    +len(node.get_publishers_info_by_topic("/safety/scan"))}
    finally:
        if node is not None:
            node.destroy_node()
        if ctx.ok():
            rclpy.shutdown(context=ctx)

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--requested",default="")
    a=p.parse_args(argv)
    if a.requested:
        try:
            requested=int(a.requested)
            if not 0<=requested<=101:
                raise ValueError("DOMAIN_OUT_OF_RANGE")
            options=[requested]
        except ValueError:
            v={"schema":"axia.g07.task04.clean_ros_domain_v1",
               "status":"INVALID_EXPLICIT_DOMAIN","domain_id":None,
               "goal_sent":False,"candidates":[]}
            a.output.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
            print("AXIA_G07_OWNER_BAD_ROS_DOMAIN",file=sys.stderr)
            return 3
    else:
        # Never silently reuse fixed old domain 86; sample valid local DDS
        # domains. If every candidate is occupied, fail without a Goal.
        options=secrets.SystemRandom().sample([n for n in range(20,102) if n!=86],8)
    v=choose_domain(options,probe_rclpy)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(v,indent=2,sort_keys=True)+"\n")
    if v["status"]!="SELECTED":
        print("AXIA_G07_OWNER_NO_CLEAN_ROS_DOMAIN",file=sys.stderr)
        return 3
    print(v["domain_id"])
    return 0

if __name__=="__main__":
    sys.exit(main())
