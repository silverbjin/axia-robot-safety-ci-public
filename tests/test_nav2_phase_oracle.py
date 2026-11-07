import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from private_nav2_phase_oracle import classify_nav2_shutdown_phase


class TestNav2PhaseOracle(unittest.TestCase):
    def test_partial_localization_cleanup_is_not_accepted(self):
        log = '''[lifecycle_manager_localization] Shutting down managed nodes...
    [INFO] [lifecycle_manager_localization]: Deactivate, cleanup, and shutdown nodes
    [INFO] [lifecycle_manager_localization]: Deactivating amcl
    [INFO] [lifecycle_manager_localization]: Cleaning up amcl
    [INFO] [lifecycle_manager_localization]: Cleaning up map_server
    '''
        out = classify_nav2_shutdown_phase(log)['localization']
        assert out == {'shutdown_started': True, 'shutdown_completed': False,
                       'last_phase': 'CLEANUP', 'last_node': 'map_server', 'transitions': 3}

    def test_completed_localization_shutdown_is_observation_not_acceptance(self):
        log = '''[lifecycle_manager_localization]: Shutting down managed nodes...
    [lifecycle_manager_localization]: Shutting down amcl
    [lifecycle_manager_localization]: Shutting down map_server
    [lifecycle_manager_localization]: Managed nodes have been shut down
    '''
        out = classify_nav2_shutdown_phase(log)
        assert out['localization']['shutdown_completed'] is True
        assert out['localization']['last_phase'] == 'FINALIZED'
        assert out['gate_accepted'] is False

    def test_navigation_and_localization_do_not_mix(self):
        log='''[lifecycle_manager_navigation]: Shutting down managed nodes...
    [lifecycle_manager_navigation]: Deactivating controller_server
    [lifecycle_manager_localization]: Shutting down managed nodes...
    [lifecycle_manager_localization]: Deactivating amcl
    '''
        out=classify_nav2_shutdown_phase(log)
        assert out['navigation']['last_node']=='controller_server'
        assert out['localization']['last_node']=='amcl'
        assert out['navigation']['last_phase']=='DEACTIVATE'

    def test_private_untrusted_payload_never_escapes(self):
        secret='PRIVATE_ROBOT_SOURCE_PASSWORD_1234'
        log=f'''[lifecycle_manager_localization]: Shutting down managed nodes...
    [lifecycle_manager_localization]: Deactivating {secret}
    [unknown.logger]: Cleaning up {secret}
    [lifecycle_manager_localization]: Shutting down {secret}
    '''
        out=classify_nav2_shutdown_phase(log)
        assert secret not in str(out)
        assert out['localization']['last_node']=='UNRECOGNIZED'
        assert out['localization']['last_phase']=='SHUTDOWN'
        assert out['gate_accepted'] is False

    def test_startup_only_does_not_claim_shutdown(self):
        out=classify_nav2_shutdown_phase('[lifecycle_manager_localization]: Activating amcl')
        assert out['localization']['shutdown_started'] is False
        assert out['localization']['shutdown_completed'] is False
        assert out['localization']['last_phase']=='NOT_OBSERVED'

    def test_missing_log_is_fail_closed(self):
        out=classify_nav2_shutdown_phase('')
        assert not out['navigation']['shutdown_completed']
        assert out['localization']['last_node']=='NOT_OBSERVED'
