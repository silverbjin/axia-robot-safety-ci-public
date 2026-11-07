#!/usr/bin/env python3
"""Sealed exact-SHA Jazzy, P0 no-sim, DDS, live fake trace for PR #52.

No Gazebo, real /axia/safety/start, Goal, Fault injector, raw upload,
or output of private stdout, exceptions, tracebacks and JUnit.
Private CI billing remains an unrelated account-level issue.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import private_ci_bridge as bridge
from private_pr52_python_ci import junit_failure_fingerprints

PIN = 'e2eb300c8e4967372daaf52944ec67fbe0c8f6b1'
_ORIGINAL_BRIDGE_PIN = 'd86ee9860de8924f6a5b2c5828d493fb7ef7f9eb'
_FILES = {
    'P0_JAZZY_SAFE_LAUNCH': ['tests/p0/test_safe_launch_ros.py'],
    'JAZZY_MIDDLEWARE': list(bridge.DDS_FILES),
    'ROS_LIVE_FAKE_INPUT': [
        'tests/ros_integration/test_p1_t08_live.py',
        'tests/ros_integration/test_p1_t08_shutdown.py',
    ],
}


def run(root: Path) -> int:
    report={'status':'JAZZY_NO_MOTION_BLOCKED','private_sha_verified':False,
            'native_private_actions_fixed':False,'gate_accepted':False,
            'goal_sent':False,'fault_injected':False,'gazebo_executed':False,
            'certified_estop_verified':False,'stages':[]}
    try:
        if bridge.PIN != _ORIGINAL_BRIDGE_PIN:
            raise bridge.GateBlocked('UNEXPECTED_SHARED_BRIDGE_PIN')
        # Read-only exact SHA contract for this one isolated public CI process.
        bridge.PIN=PIN
        private=bridge.validate_private_commit(root)
        report['private_sha_verified']=True
        env=bridge.private_runtime_env(private,os.environ)
        env['GITHUB_SHA']=PIN
        env['AXIA_P0_SIM_ONLY']='1'
        with tempfile.TemporaryDirectory(prefix='axia_pr52_jazzy_safe_',
                dir=os.environ.get('RUNNER_TEMP') or None) as temp:
            folder=Path(temp)
            setup=bridge.ros_workspace_build(private,env,folder)
            for i,(stage,files) in enumerate(_FILES.items()):
                junit=folder/(stage+'.xml')
                localenv=dict(env,ROS_DOMAIN_ID=str(166+i),
                              ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST')
                command=bridge.bash_with_ros_overlay(
                    setup,['python3','-m','pytest','-q',*files,
                           '--junitxml='+str(junit)])
                try:
                    result=bridge.scrubbed_run(stage,command,private,
                                              localenv,folder,240,junit)
                    counts={k:result.get(k,0) for k in
                            ('tests','failures','errors','skipped')}
                    report['stages'].append({'stage':stage,'status':'PASS',
                                             **counts})
                except bridge.GateBlocked:
                    summary=junit_failure_fingerprints(junit)
                    report['stages'].append({'stage':stage,'status':'BLOCKED',
                                             'redacted':summary})
                    raise
            # GitHub P0 preflight --show-args is construction ONLY; launch
            # is never started and no simulator or goal is created.
            safe_args=['bash','-lc',
                       'source /opt/ros/jazzy/setup.bash && '
                       'ros2 launch ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p0.launch.py '
                       '--show-args >/dev/null']
            bridge.scrubbed_run('P0_JAZZY_LAUNCH_ARGS',safe_args,
                               private,env,folder,75)
            report['stages'].append({'stage':'P0_JAZZY_LAUNCH_ARGS','status':'PASS'})
        report['status']='JAZZY_NO_MOTION_PASS'
    except bridge.GateBlocked:
        report['reason']='PRIVATE_GATE_BLOCKED'
    except Exception:
        report['reason']='PRIVATE_RUNNER_ERROR'
    print('AXIA_PR52_JAZZY '+json.dumps(report,sort_keys=True),flush=True)
    return 0 if report['status']=='JAZZY_NO_MOTION_PASS' else 3


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--private-root',type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(run(a.private_root))
