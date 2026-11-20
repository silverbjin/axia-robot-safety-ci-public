"""D07 exact existing ROS 2 invalid WaitSet shutdown classifier scope.

Real 'Destroyable ... destruction was requested' warning had no verified
matching context/type/stack. This guards against broad exception suppression;
it is NOT a crash fix, ROS L1 test, or the field warning root-cause proof.
"""
import importlib.util
from pathlib import Path
import unittest


def existing():
    root=Path(__file__).resolve().parents[2]
    student=root/"student" if (root/"student").is_dir() else root.parent/"student"
    src=student/"block_B/day07/h01_runtime/ros2_ws/src/axia_safety_supervisor/axia_safety_supervisor/p2_shutdown_context.py"
    if not src.is_file():
        raise AssertionError("PINNED_STUDENT_EXACT_CONTEXT_CLASSIFIER_MISSING")
    spec=importlib.util.spec_from_file_location("p2_shutdown_context_verified",src)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.is_context_waitset_shutdown


class OnlyShutdownWaitsetRace(unittest.TestCase):
    def setUp(self):
        self.classify=existing()
        self.message="failed to initialize wait set: context is not valid"

    def test_only_exact_invalidated_rclpy_context_is_ignored(self):
        class RCLError(Exception): pass
        self.assertTrue(self.classify(RCLError(self.message),context_ok=False))
        self.assertFalse(self.classify(RCLError(self.message),context_ok=True))
        self.assertFalse(self.classify(RCLError(self.message),context_ok=None))

    def test_future_destroyable_warning_is_not_misclassified(self):
        class RCLError(Exception): pass
        class InvalidHandle(Exception): pass
        msg="cannot use Destroyable because destruction was requested"
        for exc in (RCLError(msg),InvalidHandle(msg),RuntimeError(msg)):
            self.assertFalse(self.classify(exc,context_ok=False))

    def test_other_critical_rcl_errors_are_never_suppressed(self):
        class RCLError(Exception): pass
        for msg in ("failed to publish: context is not valid",
                    "failed to initialize wait set: invalid handle",
                    "failed to create client: context is not valid",
                    "cannot initialize wait set due to DDS transport"):
            self.assertFalse(self.classify(RCLError(msg),context_ok=False))

    def test_non_rclerror_same_message_is_not_swallowed(self):
        class RuntimeErrorWithMessage(Exception): pass
        self.assertFalse(self.classify(
            RuntimeErrorWithMessage(self.message),context_ok=False))


if __name__=="__main__":
    unittest.main()
