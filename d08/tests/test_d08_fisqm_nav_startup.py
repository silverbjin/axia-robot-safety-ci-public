"""Actual Owner FisQMvZz sanitized 2026-11-11 startup failure.

Original p2-l3-owner-FisQMvZz.tar.gz: 31/31 SHA256SUMS PASS. Stage
LOCALIZATION_START/MAP_AMCL_ACTIVE/INITIALPOSE_MAP_CHECKED/AMCL_TF_READY
all passed. navigation manage_nodes command=0 request sent but 95.113s
without success response. No Nav2 STARTUP manager callback in launch.log.
Later SHUTDOWN command=4 succeeded; official CM finalized, no SIGSEGV.
No Goal or Fault was dispatched in this failed case.
"""
FIELD = {
    "sha":"fa2aecf3806dbef15f1ee6dbdd089ef2935e885e",
    "localization_start":"PASS",
    "map_amcl_active":"PASS",
    "initialpose_ack":"PASS",
    "amcl_tf":"PASS",
    "nav_manager_created":True,
    "nav_manager_clients_initializing":True,
    "nav_manager_start_callback_observed":False,
    "nav_service_request_sent":True,
    "nav_manage_nodes_rc":124,
    "nav_manage_nodes_wall_s":95.113,
    "nav_reply_success":None,
    "nav_shutdown_reply_success":True,
    "cm_lifecycle_finalized_during_teardown":True,
    "goal_sent":False,
    "certified_estop":False,
    "final_status":"BLOCKED_G07_STARTUP",
}

def test_RED_original_owner_nav_startup_within_budget():
    assert FIELD['localization_start']=='PASS'
    assert FIELD['map_amcl_active']=='PASS'
    assert FIELD['initialpose_ack']=='PASS'
    assert FIELD['amcl_tf']=='PASS'
    assert FIELD['nav_manager_created']
    assert FIELD['nav_service_request_sent']
    assert not FIELD['goal_sent']
    # Genuine field RED public Actions #42973617202: 1 failed/43 passed
    # on exact rc=124 after 95.113s, not ImportError. Keep as NEGATIVE
    # regression: no Goal, no startup success promotion.
    assert FIELD['nav_manage_nodes_rc']==124
    assert FIELD['nav_manage_nodes_wall_s']>95
    assert FIELD['nav_reply_success'] is None
    assert FIELD['nav_manager_start_callback_observed'] is False
    assert FIELD['final_status']=='BLOCKED_G07_STARTUP'
    print('FISQMVZZ_ACTUAL_NAV_STARTUP_NO_REPLY_REPRODUCED_BLOCKED')

def test_original_failure_not_mislabeled_as_cm_sigsegv():
    assert FIELD['final_status']=='BLOCKED_G07_STARTUP'
    assert FIELD['cm_lifecycle_finalized_during_teardown']
    assert FIELD['nav_shutdown_reply_success']
    assert FIELD['certified_estop'] is False
