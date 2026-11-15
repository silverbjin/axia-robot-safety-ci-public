#!/usr/bin/env python3
"""Real ROS DDS pub/sub/period/STALE-level probe, not any Safety Guard TTL test."""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--events',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--messages',type=int,default=8)
    args=p.parse_args()
    import rclpy
    from rclpy.node import Node
    from diagnostic_msgs.msg import DiagnosticArray,DiagnosticStatus
    from event_contract import TOPIC
    if args.messages<4:raise ValueError('need four or more actual messages')
    args.out.mkdir(parents=True,exist_ok=True)
    rclpy.init()
    listener=Node('axia_c05_l1_listener')
    observed=[];seen_at=[];pub=None
    def got(msg):
        if msg.status:
            observed.append({'stamp_sec':msg.header.stamp.sec,'stamp_nanosec':msg.header.stamp.nanosec,
                             'level':int(msg.status[0].level),'message':msg.status[0].message,
                             'name':msg.status[0].name,'keys':{p.key:p.value for p in msg.status[0].values}})
            seen_at.append(time.monotonic_ns())
    sub=listener.create_subscription(DiagnosticArray,TOPIC,got,10)
    cmd=[sys.executable,'-u',str(Path(__file__).with_name('ros_diagnostic_bridge.py')),
         '--events',str(args.events),'--period-sec','0.1','--max-messages',str(args.messages)]
    try:
        # Listen first, launch read-only publisher process second.
        pub=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=os.environ.copy())
        deadline=time.monotonic()+25
        while len(observed)<args.messages and time.monotonic()<deadline:
            rclpy.spin_once(listener,timeout_sec=.1)
            if pub.poll() not in (None,0):break
        if pub.poll() is None:
            try:pub.wait(timeout=3)
            except subprocess.TimeoutExpired:pub.terminate();pub.wait(timeout=3)
        out,err=pub.communicate(timeout=3)
        periods=[(b-a)/1e6 for a,b in zip(seen_at,seen_at[1:])]
        topics=dict(listener.get_topic_names_and_types())
        count={name:len(listener.get_publishers_info_by_topic(name)) for name in
               ('/cmd_vel','/cmd_vel_smoothed','/cmd_vel_supervised','/cmd_vel_raw')}
        ok=(pub.returncode==0 and len(observed)==args.messages and
            'diagnostic_msgs/msg/DiagnosticArray' in topics.get(TOPIC,[]) and
            all(x['stamp_sec']>=0 and x['stamp_nanosec']>=0 for x in observed) and
            {0,1,2,3}.issubset({x['level'] for x in observed}) and
            all(x['keys'].get('control_authority')=='False' and x['keys'].get('certified_estop')=='False' for x in observed) and
            all('EDUCATION ONLY' in x['message'] for x in observed) and
            all(v==0 for v in count.values()) and
            periods and min(periods)>=20 and max(periods)<=600)
        verdict={'status':'PASS_REAL_ROS_L1_EDUCATION_ONLY' if ok else 'FAIL_REAL_ROS_L1',
                 'source':'SYNTHETIC_COURSE_FIXTURE','topic':TOPIC,'ros_actual':True,'gazebo_actual':False,
                 'goal_sent':False,'cmd_vel_published':False,'cmd_vel_publisher_count':count,
                 'sample_count':len(observed),'expected_count':args.messages,
                 'period_target_ms':100,'period_min_ms':min(periods) if periods else None,
                 'period_max_ms':max(periods) if periods else None,
                 'production_guard_ttl_verified':False,'owner_wsl2_verified':False,
                 'pub_rc':pub.returncode,'levels':sorted({x['level'] for x in observed})}
        (args.out/'verdict.json').write_text(json.dumps(verdict,indent=2,sort_keys=True)+'\n')
        (args.out/'samples.json').write_text(json.dumps(observed,indent=2,sort_keys=True)+'\n')
        (args.out/'publisher.stdout.log').write_text(out)
        (args.out/'publisher.stderr.log').write_text(err)
        print('C05_REAL_ROS_L1 '+json.dumps(verdict,sort_keys=True),flush=True)
        return 0 if ok else 1
    finally:
        if pub and pub.poll() is None:
            pub.terminate()
            try:pub.wait(timeout=3)
            except subprocess.TimeoutExpired:pub.kill();pub.wait(timeout=3)
        listener.destroy_node()
        if rclpy.ok():rclpy.shutdown()

if __name__=='__main__':raise SystemExit(main())
