#!/usr/bin/env python3
"""PUBLIC L1: real Jazzy image_view GUI survives launch parent exit, then stops.

No private Instructor, Nav2 Goal, Gazebo or actual YOLO model. This isolates
the precisely reproduced process ownership boundary with a real ROS 2 GUI.
Run under Xvfb via GitHub Actions; WSLg remains separately unverified.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from d04_owned_gui_shutdown import stop_owned, _members

import rclpy
from sensor_msgs.msg import Image


def windows():
    try:
        result=subprocess.run(["xwininfo","-root","-tree"],text=True,
                              capture_output=True,timeout=4,check=False)
        return result.stdout
    except (OSError,subprocess.TimeoutExpired):
        return ""


def main() -> int:
    rclpy.init()
    node=rclpy.create_node("d04_public_image_view_rgb_publisher")
    pub=node.create_publisher(Image,"/camera/image_raw",10)
    msg=Image()
    msg.height=160
    msg.width=200
    msg.encoding="rgb8"
    msg.step=600
    msg.data=bytes([30,90,200])* (200*160)
    # Real image_view becomes an OS window after first ROS Image delivery.
    parent=subprocess.Popen(
        [sys.executable,"-c",
         "import subprocess;"
         "c=subprocess.Popen(['ros2','run','image_view','image_view',"
         "'--ros-args','-r','image:=/camera/image_raw'],"
         "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,"
         "stderr=subprocess.DEVNULL);"
         "print(c.pid,flush=True)"],
        start_new_session=True,stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    child=int(parent.stdout.readline())
    parent.wait(timeout=6)
    evidence={}
    seen_window=False
    try:
        until=time.monotonic()+24
        while time.monotonic()<until:
            msg.header.stamp=node.get_clock().now().to_msg()
            pub.publish(msg)
            tree=windows()
            if "image_view" in tree.lower():
                seen_window=True
                break
            if not _members(parent.pid):
                raise AssertionError("D04_PUBLIC_IMAGE_VIEW_EXITED_BEFORE_DISPLAY")
            time.sleep(0.25)
        if not seen_window:
            print("D04_PUBLIC_IMAGE_VIEW_WINDOW_NOT_DETECTED",flush=True)
            print(windows()[-2000:],flush=True)
            return 2
        print("D04_PUBLIC_REAL_IMAGE_VIEW_WINDOW_OPEN child="+str(child),flush=True)
        assert parent.poll() is not None
        stop_owned([("package_launch",parent)],evidence,
                   interrupt_timeout=4,terminate_timeout=3,kill_timeout=2)
        if _members(parent.pid):
            print("D04_PUBLIC_IMAGE_VIEW_ORPHANS_REMAIN",evidence,flush=True)
            return 3
        # Window should disappear after all processes in the owned session.
        limit=time.monotonic()+5
        while time.monotonic()<limit and "image_view" in windows().lower():
            time.sleep(0.2)
        if "image_view" in windows().lower():
            print("D04_PUBLIC_REAL_IMAGE_VIEW_WINDOW_REOPENED",flush=True)
            return 4
        assert evidence["shutdown_group_audit"]["package_launch"]["parent_already_exited"]
        assert evidence["shutdown_group_audit"]["package_launch"]["residual_count"] == 0
        print("D04_PUBLIC_REAL_JAZZY_IMAGE_VIEW_SHUTDOWN_PASS",flush=True)
        print("D04_USER_WSL2_GAZEBO_YOLO_GUI=NOT_RUN_IN_THIS_JOB",flush=True)
        return 0
    finally:
        try:
            os.killpg(parent.pid,signal.SIGKILL)
        except ProcessLookupError:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__=="__main__":
    raise SystemExit(main())
