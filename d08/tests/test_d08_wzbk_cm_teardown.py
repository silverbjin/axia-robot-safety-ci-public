"""wZBKMnXa: actual Owner G07 numeric candidate but native CM exit -11.

Only field event order + publicly-safe process exit metadata. The ROS
Nav2 executable and private instructor solution are NOT copied here.
"""
# Physical/ROS observations in Owner custody; stop is a numerical candidate,
# NOT formally collision-free or certified E-Stop.
OWNER={
    "slow_distance_m":0.5488938689231873,
    "stop_distance_m":0.36110231280326843,
    "slow_vin":0.0854928120970726,
    "slow_vout":0.025585106760263442,
    "stop_vin":0.08458214998245239,
    "stop_vout":0.0,
    "odom_zero_dwell_sec":10.126115691999985,
    "candidate":True,
    "manager_ack":True,
    "cm_sigint_received":True,
    "cm_deactivating":True,
    "cm_cleaning_up":True,
    "cm_polygon_destroyed":True,
    "cm_transform_error_during_cleanup":True,
    "cm_scan_destroyed":True,
    "cm_process_exit_code":-11,
    "original_final_status":"BLOCKED_G07_CM_TEARDOWN_SIGSEGV",
    "certified_estop":False,
}

def test_actual_owner_native_cm_sigsegv_blocks_numerical_acceptance():
    assert OWNER["candidate"] is True
    assert .4<OWNER["slow_distance_m"]<.75
    assert .14<=OWNER["stop_distance_m"]<.4
    assert OWNER["stop_vout"]==0.0 and OWNER["odom_zero_dwell_sec"]>10
    assert OWNER["manager_ack"] is True
    assert OWNER["cm_sigint_received"] and OWNER["cm_cleaning_up"]
    assert OWNER["cm_scan_destroyed"] and OWNER["cm_transform_error_during_cleanup"]
    # RED public Actions #42969303180: actual exit -11 failed
    # (1 failed, 41 passed), not a missing module or fake ROS.
    # Preserve the field failure as a NEGATIVE regression: never promote
    # an actual native SIGSEGV to a clean G07 acceptance.
    assert OWNER["cm_process_exit_code"]==-11
    assert OWNER["original_final_status"]=="BLOCKED_G07_CM_TEARDOWN_SIGSEGV"
    assert OWNER["manager_ack"] is True  # message alone is not CM exit proof
    assert OWNER["certified_estop"] is False

def test_original_owner_correctly_refused_certified_acceptance():
    assert OWNER["cm_process_exit_code"]==-11
    assert OWNER["original_final_status"]=="BLOCKED_G07_CM_TEARDOWN_SIGSEGV"
    assert OWNER["certified_estop"] is False
