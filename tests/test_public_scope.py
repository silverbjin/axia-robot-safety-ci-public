"""Static scope checks, not a replacement for an independent security review."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_gazebo_script_has_no_goal_or_fault_api_invocations():
    source = (ROOT / 'scripts/gazebo_readonly_baseline.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    assert all('NavigateToPose' not in ast.dump(node)
               for node in ast.walk(tree) if isinstance(node, ast.Call))
    assert "'cmd_vel'" not in source
    assert "'fault_inject'" not in source


def test_public_repo_has_no_private_code_directory():
    for bad in ('ros2_ws/src/axia_safety_supervisor', 'hidden_tests', '.git'):
        assert not (ROOT / bad).exists()


def test_scan_report_never_promotes_to_acceptance():
    from axia_public_contracts.scan import summarize_receive_gaps
    assert summarize_receive_gaps([0.0, 0.1])['gate_accepted'] is False
