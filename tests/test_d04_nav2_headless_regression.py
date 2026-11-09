"""Regression: official Jazzy Nav2 PythonExpression cannot evaluate lower-case false.

Do not bypass P1 command topology, change the baseline or fake a ROS graph.
"""
import ast
from pathlib import Path

PRIVATE = Path(__file__).resolve().parents[1]
LAUNCH = PRIVATE/"d04/axia_d04_vision_demo/launch/d04_p1_yolo.launch.py"
RUNNER = PRIVATE/"scripts/d04_packaged_p1_yolo_gate.py"


def test_real_nav2_expression_is_python_boolean_case_sensitive():
    # Official Nav2 Jazzy tb3_simulation_launch.py:
    # PythonExpression([use_simulator, ' and not ', headless])
    assert eval("True and not False") is True
    try:
        eval("True and not false")
    except NameError:
        pass
    else:
        raise AssertionError("Actual Nav2 must not silently accept false")


def test_d04_uses_case_normalizing_Python_bool_forwarder():
    source=LAUNCH.read_text()
    assert 'normalize_nav2_boolean' in source
    assert '"headless": normalize_nav2_boolean' in source
    assert 'default_value="True"' in source
    assert 'LaunchConfiguration("headless")' in source


def test_runner_passes_canonical_nav2_bool_without_faking_gui():
    source=RUNNER.read_text()
    assert '"headless:=" + ("False" if gui else "True")' in source
    assert 'show_image:=' in source
    assert 'create_publisher(' not in source
    assert 'send_goal_async(' not in source


def test_no_lowercase_bools_sent_to_upstream_nav2():
    source=LAUNCH.read_text()
    assert '"headless": LaunchConfiguration("headless")' not in source
    assert '"use_simulator": "False"' not in source
