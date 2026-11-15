#!/usr/bin/env python3
"""ROS 2 Jazzy educational DiagnosticArray publisher: never a safety controller.

Publishes to /axia/education/diagnostics only; never to /diagnostics, cmd_vel, Nav2.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from event_contract import EventGate,to_diagnostic_payload,validate_event,TOPIC


def run_ros(events_path:Path,period_sec=0.1,max_messages=12):
    import rclpy
    from rclpy.node import Node
    from diagnostic_msgs.msg import DiagnosticArray,DiagnosticStatus,KeyValue
    from std_msgs.msg import String
    events=[json.loads(line) for line in Path(events_path).read_text(encoding='utf-8').splitlines() if line.strip()]
    if not events:raise ValueError('empty educational events')
    for event in events:validate_event(event)
    if period_sec<0.05 or period_sec>2.0 or max_messages<1:raise ValueError('unsafe demo rate/count')
    rclpy.init()
    class Bridge(Node):
        def __init__(self):
            super().__init__('axia_block_c_diagnostics')
            self.pub=self.create_publisher(DiagnosticArray,TOPIC,10)
            self.gate=EventGate(stale_after_ns=2_000_000_000)
            self.issued=0;self.finished=False;self.end_at=None
            self.start_at=time.monotonic()
            # Optional READ-ONLY context; no parameters/actions/services create control authority.
            self.safety_subscription=self.create_subscription(String,'/axia/safety/state',lambda m:None,10)
            self.fault_subscription=self.create_subscription(String,'/axia/fault/status',lambda m:None,10)
            self.timer=self.create_timer(period_sec,self.tick)
        def tick(self):
            if self.pub.get_subscription_count()==0 and time.monotonic()-self.start_at<3.0:
                return  # wait briefly for actual ROS DDS subscription matching
            if self.issued>=min(len(events),max_messages):
                if self.end_at is None:self.end_at=time.monotonic()+0.35
                if time.monotonic()>=self.end_at:self.finished=True
                return
            event=events[self.issued]
            now_mono=time.monotonic_ns();now_wall=time.time_ns()
            self.gate.accept(event,arrival_mono_ns=now_mono,arrival_wall_ns=now_wall)
            view=to_diagnostic_payload(event)
            status=DiagnosticStatus();status.name='AXIA Block C Synthetic Anomaly (EDUCATION ONLY)'
            status.level=view['level'];status.message=view['message'];status.hardware_id=view['hardware_id']
            vals={k:v for k,v in view.items() if k not in ('topic','level','message','hardware_id')}
            vals['ingress_monotonic_ns']=now_mono;vals['ingress_wall_ns']=now_wall
            status.values=[KeyValue(key=str(k),value='' if v is None else str(v)) for k,v in vals.items()]
            msg=DiagnosticArray();msg.header.stamp=self.get_clock().now().to_msg();msg.status=[status]
            self.pub.publish(msg);self.issued+=1
    node=Bridge()
    try:
        while rclpy.ok() and not node.finished:rclpy.spin_once(node,timeout_sec=0.1)
        print(f'C05_ROS_PUBLISH_DONE topic={TOPIC} count={node.issued} actual_ros=true no_goal=true no_cmd_vel=true',flush=True)
    finally:
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()


def main():
    p=argparse.ArgumentParser();p.add_argument('--events',type=Path,required=True)
    p.add_argument('--period-sec',type=float,default=0.1);p.add_argument('--max-messages',type=int,default=12)
    x=p.parse_args();run_ros(x.events,x.period_sec,x.max_messages)

if __name__=='__main__':main()
