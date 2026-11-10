"""MVP component readiness must never masquerade as formal physical safety acceptance."""
from p2_mvp.gate import assess, VERIFIED_COMPONENT_EVIDENCE


def test_actual_sealed_components_do_not_require_g06_replay():
    status = assess(VERIFIED_COMPONENT_EVIDENCE)
    assert status['status'] == 'MVP_DEMO_COMPONENT_READY'
    assert status['g06_retest_required'] is False
    assert status['formal_gate_accepted'] is False
    assert status['mvp_demo_observed'] is False
    assert status['certified_estop'] is False
    assert status['g07_integrated_goal_e2e'] is False
    assert status['collision_ground_truth'] is False


def test_missing_gazebo_obstacle_ack_blocks_component_preparation():
    import copy
    ev = copy.deepcopy(VERIFIED_COMPONENT_EVIDENCE)
    ev['g07_l2']['set_pose_ack'] = False
    assert assess(ev)['status'] == 'HOLD'


def test_missing_real_cm_stop_blocks_component_preparation():
    import copy
    ev = copy.deepcopy(VERIFIED_COMPONENT_EVIDENCE)
    ev['cm_l1']['stop_output_mps'] = 0.18
    assert assess(ev)['status'] == 'HOLD'


def test_not_permitted_to_claim_integration_or_estop():
    import copy
    for key in ('certified_estop', 'mvp_demo_observed', 'formal_gate_accepted'):
        ev = copy.deepcopy(VERIFIED_COMPONENT_EVIDENCE)
        ev[key] = True
        assert assess(ev)['status'] == 'HOLD'


def test_not_permitted_to_fake_contact_or_goal_proof():
    import copy
    for key, val in [('collision_ground_truth', True), ('goal_sent', True)]:
        ev = copy.deepcopy(VERIFIED_COMPONENT_EVIDENCE)
        ev['g07_l2'][key] = val
        assert assess(ev)['status'] == 'HOLD'


def test_actual_evidence_sources_are_not_arbitrary_values():
    import copy
    ev = copy.deepcopy(VERIFIED_COMPONENT_EVIDENCE)
    ev['g07_l2']['private_sha'] = '0'*40
    assert assess(ev)['status'] == 'HOLD'
    ev = copy.deepcopy(VERIFIED_COMPONENT_EVIDENCE)
    ev['cm_l1']['run_id'] = 123
    assert assess(ev)['status'] == 'HOLD'
