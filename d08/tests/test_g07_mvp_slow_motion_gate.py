"""Numeric reconstruction of user's actual G07 Gazebo/ROS evidence on 2026-11-10."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from p2_mvp_slow_motion_gate import admit_g07_mvp_slow_motion as check

def scene():
    snap={'mono':100.,'final_publishers':[('axia_base_command_guard','geometry_msgs/msg/Twist')],
          'goal_uuid':'caff4c4a9c35491d9988204024b30ba3','action_status':2,
          'guard':{'latched':False,'reason':'FORWARDING_MONITORED_CM'},
          'clock_advancing':True,'action_at':99.,
          'odom_speed':.0394,'final_speed':.0394,'pre_guard_speed':.0394}
    for k in ('scan','odom','guard','supervisor','clock','final','pre_guard','supervised'):
        snap[k+'_at']=99.95
    data={'scan':.665,'vin':[{'t':99.94,'vx':.1314,'wz':0.}],
          'pre':[{'t':99.95,'vx':.0394,'wz':0.}]}
    return snap,data

def test_real_g07_slowzone_0394_is_actual_movement():
    s,d=scene()
    assert check(s,d)==(True,'G07_MVP_ACTUAL_GUARDED_SLOWZONE_MOTION')

def test_invalid_stopped_stale_unowned_or_unmonitored_rejected():
    for key,value in [('odom_speed',0.),('final_speed',0.),('pre_guard_speed',0.),
                      ('action_status',4),('goal_uuid',None),
                      ('scan_at',98.),('odom_at',98.),('clock_advancing',False),
                      ('final_publishers',[])]:
        s,d=scene();s[key]=value
        assert not check(s,d)[0],key
    s,d=scene();s['guard']['latched']=True;assert not check(s,d)[0]
    s,d=scene();s['guard']['reason']='NO_FRESH_PAIR';assert not check(s,d)[0]
    s,d=scene();d['scan']=.39;assert not check(s,d)[0]
    s,d=scene();d['scan']=.8;assert not check(s,d)[0]
    s,d=scene();d['pre'][-1]['vx']=.10;assert not check(s,d)[0]
    s,d=scene();d['pre'][-1]['t']=98;assert not check(s,d)[0]
    s,d=scene();s['odom_speed']=.17;assert not check(s,d)[0]

def test_actual_later_slow_zone_0185_not_zero():
    s,d=scene()
    s['odom_speed']=s['final_speed']=s['pre_guard_speed']=.0185
    d['vin'][-1]['vx']=.0617;d['pre'][-1]['vx']=.0185
    assert check(s,d)[0]
    s['odom_speed']=s['final_speed']=s['pre_guard_speed']=0.
    d['pre'][-1]['vx']=0.
    assert not check(s,d)[0]
