"""Read-only classify native Jazzy EventsExecutor spin-thread first failure.

The native 0/2 L2 #44861540326 had worker SystemError before later
CI_MOVING_GOAL_TIMEOUT_HEALTH. Neither signal proves C++/DDS causal root.
No ROS imports, Goal, safety pass, TTL changes or private data.
"""

def classify(lines):
    result={"schema":"axia.g07.events_executor_first_abort.v1",
            "first_failure":"EVENTS_EXECUTOR_FIRST_FAILURE_UNVERIFIED_HOLD",
            "secondary_failure":None,
            "root_cause_proven":False,"certified_estop":False,
            "owner_l3_accepted":False,"actual_goal_accepted":False,
            "release":"HOLD"}
    if not isinstance(lines,(list,tuple)) or len(lines)>20000:
        return result
    worker=False
    events_spin_at=None
    health_at=None
    actual_jazzy_l1_script_at=None
    l1_spin_once_at=None
    l1_systemerror_at=None
    for i,row in enumerate(lines):
        if not isinstance(row,str):
            return result
        if "AXIA_G07_MOVING_EVENTS_EXECUTOR_AB=CI_ONLY" in row:
            worker=True
        if (worker and "SystemError: null argument to internal routine" in row
                and events_spin_at is None):
            events_spin_at=i
        if "CI_MOVING_GOAL_TIMEOUT_HEALTH" in row and health_at is None:
            health_at=i
        if ("axia_g07_events_scan_messageinfo_l1.py" in row
                and actual_jazzy_l1_script_at is None):
            actual_jazzy_l1_script_at=i
        if "ex.spin_once(timeout_sec=.04)" in row and l1_spin_once_at is None:
            l1_spin_once_at=i
        if ("SystemError: null argument to internal routine" in row
                and l1_systemerror_at is None):
            l1_systemerror_at=i
    if events_spin_at is not None and (health_at is None or events_spin_at<health_at):
        result["first_failure"]="EVENTS_EXECUTOR_SPIN_WORKER_EXCEPTION_HOLD"
        if health_at is not None:
            result["secondary_failure"]="CI_MOVING_GOAL_TIMEOUT_HEALTH"
        result["native_l2_first_worker_exception_observed"]=True
    elif (actual_jazzy_l1_script_at is not None
          and l1_spin_once_at is not None
          and l1_systemerror_at is not None
          and actual_jazzy_l1_script_at<=l1_spin_once_at<l1_systemerror_at):
        # Same SystemError independently reproduced with genuine ROS Jazzy
        # 300Hz Clock + 10Hz Scan and no Gazebo/Goal. It proves this pinned
        # EventsExecutor candidate is unusable here, NOT the C++ root cause.
        result["first_failure"]="JAZZY_EVENTS_EXECUTOR_L1_SYSTEMERROR_HOLD"
        result["native_l1_no_goal_reproduction"]=True
        result["experimental_executor_release_allowed"]=False
    elif health_at is not None:
        result["first_failure"]="HEALTH_TIMEOUT_ORIGIN_UNVERIFIED_HOLD"
        result["native_l2_first_worker_exception_observed"]=False
    return result
