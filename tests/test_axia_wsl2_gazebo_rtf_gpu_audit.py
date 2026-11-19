"""L0: portable read-only WSL2/Gazebo RTF/GPU audit contracts.

Does not need ROS, GPU, Gazebo, WSLg or private instructor source.
"""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/axia_wsl2_gazebo_rtf_gpu_audit.py"


def module():
    assert SCRIPT.is_file(), "RED: no one-shot process/GPU/RTF capture script"
    spec = importlib.util.spec_from_file_location("rtf_audit", SCRIPT)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = obj
    spec.loader.exec_module(obj)
    return obj


def synthetic(rtf, start=10):
    return (
        f"sim_time {{\n sec: {start}\n nsec: 0\n}}\n"
        "real_time {\n sec: 20\n nsec: 0\n}\n"
        "paused: false\nreal_time_factor: 0.33\n"
        f"sim_time {{\n sec: {start + rtf}\n nsec: 0\n}}\n"
        "real_time {\n sec: 21\n nsec: 0\n}\n"
        "paused: false\nreal_time_factor: 0.22\n"
    )


def test_interval_rtf_not_median():
    m = module()
    assert m.parse_stats(synthetic(1))["interval_rtf_percent"] == 100.0
    assert m.parse_stats(synthetic(0))["interval_rtf_percent"] == 0.0
    assert m.parse_stats(synthetic(1))["rtf_field_median"] != 1.0


def test_paused_reset_and_missing_world_stats_do_not_claim_rtf():
    m = module()
    assert m.parse_stats("")["interval_rtf_percent"] is None
    raw = synthetic(1).replace("paused: false", "paused: true")
    assert m.parse_stats(raw)["interval_rtf_percent"] is None
    reset = synthetic(1).replace("sec: 11", "sec: 9")
    assert m.parse_stats(reset)["interval_rtf_percent"] is None


def test_child_glx_profiles_are_scoped_and_do_not_change_parent():
    m = module()
    parent = {"GALLIUM_DRIVER": "custom", "MESA_D3D12_DEFAULT_ADAPTER_NAME": "Intel",
              "LIBGL_ALWAYS_SOFTWARE": "1", "DISPLAY": ":0"}
    nvidia = m.renderer_env("d3d12_nvidia", parent)
    assert nvidia["GALLIUM_DRIVER"] == "d3d12"
    assert nvidia["MESA_D3D12_DEFAULT_ADAPTER_NAME"] == "NVIDIA"
    assert "LIBGL_ALWAYS_SOFTWARE" not in nvidia
    assert parent["LIBGL_ALWAYS_SOFTWARE"] == "1"
    default = m.renderer_env("default", parent)
    assert "GALLIUM_DRIVER" not in default
    assert "MESA_D3D12_DEFAULT_ADAPTER_NAME" not in default


def test_comparison_uses_interval_rtf_not_glx_gpu_guess():
    m = module()
    a = {"rtf": {"interval_rtf_percent": 91.8}, "server": {"gpu_env": {
        "GALLIUM_DRIVER": "", "MESA_D3D12_DEFAULT_ADAPTER_NAME": ""}},
         "sensor_profile": {"rgbd_hz_disk_candidate": 10}}
    b = {"rtf": {"interval_rtf_percent": 21.3}, "server": {"gpu_env": {
        "GALLIUM_DRIVER": "d3d12", "MESA_D3D12_DEFAULT_ADAPTER_NAME": "NVIDIA"}},
         "sensor_profile": {"rgbd_hz_disk_candidate": 30}}
    data = m.compare(a, b)
    assert data["rtf_gap_percentage_points"] == -70.5
    assert "gazebo_server_gpu_env" in data["changed_conditions"]
    assert "rgbd_hz_disk_candidate" in data["changed_conditions"]
    assert data["root_cause_confirmed"] is False


def test_cli_self_check_and_offline_artifacts(tmp_path):
    m = module()
    result = subprocess.run([sys.executable, str(SCRIPT), "--self-check"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "AXIA_RTF_GPU_AUDIT_SELF_CHECK_PASS" in result.stdout
    stats = tmp_path / "synthetic.txt"
    stats.write_text(synthetic(1), encoding="utf-8")
    output = subprocess.run([sys.executable, str(SCRIPT), "--from-stats", str(stats),
                             "--out-root", str(tmp_path / "reports")],
                            capture_output=True, text=True, timeout=15)
    assert output.returncode == 0, output.stdout + output.stderr
    dirs = list((tmp_path / "reports").glob("audit_*"))
    assert len(dirs) == 1
    summary = json.loads((dirs[0] / "summary.json").read_text())
    assert summary["capture_status"] == "SYNTHETIC_TEST_ONLY"
    assert summary["rtf"]["interval_rtf_percent"] == 100.0
    assert summary["actual_gazebo_gui_verified"] is False
    archives = list(dirs[0].glob("*.zip"))
    assert len(archives) == 1
    with zipfile.ZipFile(archives[0]) as z:
        assert "summary.json" in z.namelist()
        assert "SHA256SUMS" in z.namelist()
        assert all("environ" not in name for name in z.namelist())


def test_two_partition_servers_fail_closed_and_single_partition_is_selected():
    m = module()
    servers = [
        {"pid": 101, "role": "gazebo_server_candidate",
         "env": {"GZ_PARTITION": "axia_a"}},
        {"pid": 102, "role": "gazebo_server_candidate",
         "env": {"GZ_PARTITION": "axia_b"}},
    ]
    chosen, partition, status = m.choose_server(servers, None, None)
    assert chosen is None and partition is None
    assert status == "MULTIPLE_OR_UNIDENTIFIED_GAZEBO_PARTITIONS"
    chosen, partition, status = m.choose_server(servers, 102, None)
    assert chosen["pid"] == 102 and partition == "axia_b"
    chosen, partition, status = m.choose_server(servers, 102, "axia_a")
    assert chosen is None and status == "SERVER_PID_PARTITION_MISMATCH"


def test_server_and_gui_roles_are_not_conflated():
    m = module()
    assert m.process_role(["gz", "sim", "-s", "-r"], "gz") == "gazebo_server_candidate"
    assert m.process_role(["gz", "sim", "-g", "-v", "4"], "gz") == "gazebo_gui"
    assert m.process_role(["rviz2", "-d", "config.rviz"], "rviz2") == "rviz2"
    assert m.process_role(["bash"], "bash") is None


def test_owner_wsl2_copy_paste_download_command_is_syntax_checked():
    guide = (ROOT / "docs/AXIA_WSL2_GAZEBO_RTF_GPU_AUDIT_20261119_KO.md")
    text = guide.read_text(encoding="utf-8")
    import re
    block = re.search(r"(?ms)^~~~bash\n(.*?)\n~~~", text)
    assert block is not None
    cmd = block.group(1)
    result = subprocess.run(["bash", "-n", "-c", cmd], text=True,
                            capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert "scripts/axia_wsl2_gazebo_rtf_gpu_audit.py" in cmd
    assert "5d428e1a043e14fa88f22cdc4073d23f75ed86a5" in cmd
    assert "python3" in cmd and "--self-check" in cmd
    assert "--seconds 20" in cmd
    assert "env -u GZ_PARTITION" in cmd
    assert "python3" in text and "--compare" in text
    assert "sudo " not in cmd and "pkill " not in cmd and "git reset" not in cmd


def test_auto_selects_unique_server_with_matching_gui_despite_orphan_servers():
    """Regression from Owner ZIP A: two server partitions, only current has GUI."""
    m = module()
    processes = [
        {"pid": 5805, "role": "gazebo_server_candidate",
         "env": {"GZ_PARTITION": "axia_p2_task04_old"}},
        {"pid": 13700, "role": "gazebo_server_candidate",
         "env": {"GZ_PARTITION": "axia_p2_task04_current"}},
        {"pid": 14492, "role": "gazebo_gui",
         "env": {"GZ_PARTITION": "axia_p2_task04_current"}},
        {"pid": 14493, "role": "rviz2",
         "env": {"GZ_PARTITION": "axia_p2_task04_current"}},
    ]
    chosen, partition, status = m.choose_server(processes, None, None)
    assert chosen["pid"] == 13700
    assert partition == "axia_p2_task04_current"
    assert status == "AUTO_PAIRED_SERVER_GUI_PARTITION"


def test_auto_selects_d04_session_not_leftover_g07_when_gui_has_two_wrappers():
    """Regression from Owner ZIP B: old G07, D04 server and two D04 GUI wrappers."""
    m = module()
    processes = [
        {"pid": 5805, "role": "gazebo_server_candidate",
         "env": {"GZ_PARTITION": "axia_p2_task04_old"}},
        {"pid": 15603, "role": "gazebo_server_candidate",
         "env": {"GZ_PARTITION": "axia_d04_student_current"}},
        {"pid": 15604, "role": "gazebo_gui",
         "env": {"GZ_PARTITION": "axia_d04_student_current"}},
        {"pid": 15606, "role": "gazebo_gui",
         "env": {"GZ_PARTITION": "axia_d04_student_current"}},
    ]
    chosen, partition, status = m.choose_server(processes, None, None)
    assert chosen["pid"] == 15603
    assert partition == "axia_d04_student_current"
    assert status == "AUTO_PAIRED_SERVER_GUI_PARTITION"


def test_auto_refuses_two_simultaneous_matching_gazebo_gui_sessions():
    m = module()
    processes = [
        {"pid": 1, "role": "gazebo_server_candidate", "env": {"GZ_PARTITION": "a"}},
        {"pid": 2, "role": "gazebo_gui", "env": {"GZ_PARTITION": "a"}},
        {"pid": 3, "role": "gazebo_server_candidate", "env": {"GZ_PARTITION": "b"}},
        {"pid": 4, "role": "gazebo_gui", "env": {"GZ_PARTITION": "b"}},
    ]
    chosen, partition, status = m.choose_server(processes, None, None)
    assert chosen is None and partition is None
    assert status == "MULTIPLE_ACTIVE_GAZEBO_GUI_SESSIONS"


def test_g07_does_not_misattribute_latest_d04_camera_sdf(tmp_path):
    m = module()
    scene = tmp_path / "d04-gazebo-fake" / "scene" / "student_waffle_rgb.sdf.xacro"
    scene.parent.mkdir(parents=True)
    scene.write_text('<sdf><sensor name="axia_student_rgb" type="camera"><update_rate>30</update_rate></sensor></sdf>')
    result = m.find_disk_sensor_profile(partition="axia_p2_task04_123", base=tmp_path)
    assert result["status"] == "NOT_APPLICABLE_TO_G07_SCENARIO"
    assert result["rgbd_hz_disk_candidate"] is None


def test_d04_rgb_camera_sensor_rate_not_mistaken_for_missing_rgbd(tmp_path):
    m = module()
    scene = tmp_path / "d04-gazebo-fake" / "scene" / "student_waffle_rgb.sdf.xacro"
    scene.parent.mkdir(parents=True)
    scene.write_text(
        '<sdf><sensor name="axia_student_rgb" type="camera">'
        '<topic>camera/image_raw</topic><update_rate>30</update_rate>'
        '<camera><image><width>640</width><height>480</height></image></camera>'
        '</sensor></sdf>'
    )
    result = m.find_disk_sensor_profile(partition="axia_d04_student_123_40", base=tmp_path)
    assert result["status"] == "DISK_ONLY_NOT_PROVEN_ACTIVE"
    assert result["rgb_camera_hz_disk_candidate"] == 30.0
    assert result["camera_sensors_disk"][0]["name"] == "axia_student_rgb"
    assert result["camera_sensors_disk"][0]["resolution"] == "640x480"


def test_workload_profile_counts_only_target_partition():
    m = module()
    procs = [
        {"role": "gazebo_server_candidate", "env": {"GZ_PARTITION": "A"}},
        {"role": "gazebo_gui", "env": {"GZ_PARTITION": "A"}},
        {"role": "yolo", "env": {"GZ_PARTITION": "B"}},
        {"role": "image_view", "env": {"GZ_PARTITION": "B"}},
        {"role": "rviz2", "env": {"GZ_PARTITION": "A"}},
    ]
    assert m.count_target_roles(procs, "A") == {
        "gazebo_server_candidate": 1, "gazebo_gui": 1, "rviz2": 1}
    assert m.count_target_roles(procs, "B") == {"yolo": 1, "image_view": 1}


def test_comparison_reports_d04_rgb_camera_vs_g07_lidar_only_workload():
    m = module()
    a = {
        "rtf": {"interval_rtf_percent": 90.0},
        "sensor_profile": {"status": "NOT_APPLICABLE_TO_G07_SCENARIO",
                           "rgb_camera_hz_disk_candidate": None},
        "active_process_roles": {"gazebo_server_candidate": 1, "gazebo_gui": 1},
    }
    b = {
        "rtf": {"interval_rtf_percent": 20.0},
        "sensor_profile": {"status": "DISK_ONLY_NOT_PROVEN_ACTIVE",
                           "rgb_camera_hz_disk_candidate": 30.0},
        "active_process_roles": {"gazebo_server_candidate": 1, "gazebo_gui": 2,
                                 "yolo": 2, "image_view": 2},
    }
    out = m.compare(a, b)
    assert out["rtf_gap_percentage_points"] == -70.0
    assert "active_process_roles" in out["changed_conditions"]
    assert "rgb_camera_hz_disk_candidate" in out["changed_conditions"]
    assert "sensor_profile_scope" in out["changed_conditions"]
    assert out["root_cause_confirmed"] is False
