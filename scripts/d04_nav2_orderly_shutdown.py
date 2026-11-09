#!/usr/bin/env python3
"""Opt-in Nav2 Jazzy lifecycle shutdown before terminating D04 process groups.

This helper runs on a separate Python process, because the vision verifier
rclpy context has already been shut down. It invokes the *official* Nav2
manage_nodes service. No direct /cmd_vel publisher, Goal, Fault, or custom
E-Stop. The service must actually respond success=True to count as PASS.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import time

NAV_MANAGER="/lifecycle_manager_navigation/manage_nodes"
LOC_MANAGER="/lifecycle_manager_localization/manage_nodes"
MANAGERS=(NAV_MANAGER,LOC_MANAGER)


def orderly_shutdown(out: Path, timeout_s: float = 24) -> dict:
    import rclpy
    from nav2_msgs.srv import ManageLifecycleNodes

    out.parent.mkdir(parents=True, exist_ok=True)
    result={
        "gate":"G-D04-NAV2-LIFECYCLE-SHUTDOWN",
        "passed":False,
        "requested_order":list(MANAGERS),
        "services":{},
        "goal_sent":False,
        "fault_injected":False,
        "cmd_vel_published":False,
        "certified_estop":False,
    }
    rclpy.init()
    node = rclpy.create_node("axia_d04_orderly_shutdown")
    try:
        for name in MANAGERS:
            info={"available":False, "response_success":False}
            result["services"][name]=info
            client=node.create_client(ManageLifecycleNodes,name)
            try:
                if not client.wait_for_service(timeout_sec=5.0):
                    info["reason"]="SERVICE_NOT_FOUND"
                    continue
                info["available"]=True
                req=ManageLifecycleNodes.Request()
                req.command=ManageLifecycleNodes.Request.SHUTDOWN
                pending=client.call_async(req)
                rclpy.spin_until_future_complete(node,pending,timeout_sec=timeout_s)
                if not pending.done():
                    info["reason"]="SERVICE_TIMEOUT"
                elif pending.exception() is not None:
                    info["reason"]="SERVICE_EXCEPTION:"+type(pending.exception()).__name__
                else:
                    resp=pending.result()
                    info["response_success"]=bool(resp is not None and resp.success)
                    info["reason"]="SUCCESS" if info["response_success"] else "SERVICE_REJECTED"
            except Exception as exc:
                info["reason"]=type(exc).__name__+":"+str(exc)[:170]
            finally:
                node.destroy_client(client)
        result["passed"]=all(
            result["services"].get(x,{}).get("response_success") is True
            for x in MANAGERS)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result



def request_nav2_shutdown(env: dict, out: Path, *, timeout_s: int = 60) -> dict:
    """Run the actual service client in a fresh process with strict time bound."""
    import os
    import subprocess
    target=out/"nav2_shutdown.json"
    log=out/"nav2_shutdown.log"
    args=[
        sys.executable,str(Path(__file__).resolve()),"--out",str(target),
        "--service-timeout","24",
    ]
    try:
        result=subprocess.run(
            args,env=env,text=True,capture_output=True,
            timeout=timeout_s,check=False)
        log.write_text(result.stdout+"\n"+result.stderr,encoding="utf-8")
        payload=json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {}
        payload["client_exit_code"]=result.returncode
        payload["passed"]=bool(payload.get("passed") is True and result.returncode==0)
        return payload
    except (OSError,subprocess.TimeoutExpired,ValueError,json.JSONDecodeError) as exc:
        log.write_text("ERROR:"+type(exc).__name__+"\n",encoding="utf-8")
        return {"passed":False,"error":type(exc).__name__,"client_exit_code":None}


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--service-timeout",type=int,default=24)
    a=p.parse_args()
    try:
        result=orderly_shutdown(a.out,timeout_s=a.service_timeout)
    except Exception as exc:
        result={"gate":"G-D04-NAV2-LIFECYCLE-SHUTDOWN","passed":False,
                "error":type(exc).__name__+":"+str(exc)[:300]}
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result["passed"] else 2


if __name__=="__main__":
    raise SystemExit(main())
