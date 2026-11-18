"""D07-H01 public SIM Goal admission, no ROS or Goal in this suite."""
import unittest
from tools.d07_h01_public_contract import admit_h01


GOOD = dict(
    GITHUB_ACTIONS="true", AXIA_P0_SIM_ONLY="1",
    AXIA_G07_CI_SIM_GOAL_ALLOWED="1", AXIA_D07_H01_CI_ALLOWED="1",
    ROS_DISTRO="jazzy", GZ_PARTITION="axia_p2_d07_h01_95",
    AXIA_G07_CI_OWNER_BAG_PARITY="1",
    AXIA_G07_OWNER_STARTUP_PARITY="1"
)
SHA="a"*40
GEOMETRY=dict(status="D07_H01_REAL_NAV2_GEOMETRY_READY_NO_GOAL",
    source_sha=SHA, goal_sent=False, real_nav2=True, real_laser_scan=True,
    path_viable=True, obstacle_pose_native_ack=True,
    post_ack_scan_stamp_progressed=True, actual_costmap_obstacle_observed=True,
    path_changed=True, contact_topic_proven=True, map_frame="map")


class TestD07H01PublicAdmission(unittest.TestCase):
    def admit(self, env=GOOD, geo=GEOMETRY, **kw):
        args=dict(source_sha=SHA,checkout_sha=SHA,case="D07-H01",
                  goals=1,goal=(-1.7,0.7),geometry_report=geo)
        args.update(kw)
        return admit_h01(dict(env),**args)

    def test_one_real_sim_goal_only_with_live_geometry_evidence(self):
        self.assertTrue(self.admit())

    def test_no_extra_goal(self):
        for count in (0,2,3):
            with self.subTest(count=count),self.assertRaises(ValueError):
                self.admit(goals=count)

    def test_wrong_case_or_goal_denied(self):
        for change in (dict(case="S01"),dict(goal=(0,0)),dict(goal=(-1.7,0.6))):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.admit(**change)

    def test_no_ci_or_owner_consent_bypass(self):
        for key in GOOD:
            env=dict(GOOD)
            env[key]="0"
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.admit(env=env)
        env=dict(GOOD)
        env["AXIA_D07_H01_CI_ALLOWED"]="1"
        env["GITHUB_ACTIONS"]="false"
        with self.assertRaises(ValueError):
            self.admit(env=env)

    def test_exact_source_sha(self):
        for wrong in ("b"*40,"bad",""):
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):
                self.admit(checkout_sha=wrong)

    def test_missing_pre_goal_geometry_or_contact_is_fail_closed(self):
        for key in GEOMETRY:
            geo=dict(GEOMETRY)
            geo[key]=None
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.admit(geo=geo)

    def test_no_acceptance_from_claimed_path_without_real_scan(self):
        for key in ("real_nav2","real_laser_scan","path_viable",
                    "actual_costmap_obstacle_observed","path_changed",
                    "post_ack_scan_stamp_progressed","contact_topic_proven"):
            geo=dict(GEOMETRY);geo[key]=False
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.admit(geo=geo)


if __name__=="__main__":
    unittest.main()
