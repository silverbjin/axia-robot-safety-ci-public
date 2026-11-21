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
    if events_spin_at is not None and (health_at is None or events_spin_at<health_at):
        result["first_failure"]="EVENTS_EXECUTOR_SPIN_WORKER_EXCEPTION_HOLD"
        if health_at is not None:
            result["secondary_failure"]="CI_MOVING_GOAL_TIMEOUT_HEALTH"
        result["native_l2_first_worker_exception_observed"]=True
    elif health_at is not None:
        result["first_failure"]="HEALTH_TIMEOUT_ORIGIN_UNVERIFIED_HOLD"
        result["native_l2_first_worker_exception_observed"]=False
    return result
