#!/usr/bin/env python3
"""Jazzy rclpy DDS loopback only: synthetic message, NOT AXIA Supervisor or Gazebo."""
import json
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor
from std_msgs.msg import String


def main():
    rclpy.init()
    sender = rclpy.create_node('axia_public_ci_sender')
    receiver = rclpy.create_node('axia_public_ci_receiver')
    received = []
    publisher = sender.create_publisher(String, '/axia_public_ci/echo', 10)
    subscription = receiver.create_subscription(
        String, '/axia_public_ci/echo', lambda msg: received.append(msg.data), 10)
    executor = SingleThreadedExecutor()
    executor.add_node(sender)
    executor.add_node(receiver)
    deadline = time.monotonic() + 25.0
    try:
        while time.monotonic() < deadline and 'AXIA_PUBLIC_JAZZY_DDS_OK' not in received:
            msg = String()
            msg.data = 'AXIA_PUBLIC_JAZZY_DDS_OK'
            publisher.publish(msg)
            executor.spin_once(timeout_sec=0.1)
        passed = 'AXIA_PUBLIC_JAZZY_DDS_OK' in received
        print(json.dumps({'kind': 'actual_ros2_dds_synthetic_loopback',
                          'passed': passed, 'gazebo': 'NOT_RUN',
                          'instructor_supervisor': 'NOT_RUN',
                          'gate_accepted': False}))
        return 0 if passed else 1
    finally:
        executor.remove_node(receiver)
        executor.remove_node(sender)
        receiver.destroy_subscription(subscription)
        sender.destroy_publisher(publisher)
        receiver.destroy_node()
        sender.destroy_node()
        executor.shutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
