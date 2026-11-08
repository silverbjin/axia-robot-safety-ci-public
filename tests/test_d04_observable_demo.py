"""D04 visibility RED -> GREEN contracts: real animated Actor + visible owner stages."""
from pathlib import Path
import importlib.util
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"d04/axia_d04_vision_demo"
SCRIPTS=ROOT/"scripts"
sys.path.insert(0,str(PKG))
from axia_d04_vision_demo.overlay import make_overlay


def fixture(tmp_path):
    w=tmp_path/"waffle.sdf.xacro"
    w.write_text("""<sdf><model name="turtlebot3_waffle">
      <link name="camera_link"><sensor name="depth" type="depth"/></link>
      <plugin name="control"><topic>/cmd_vel</topic></plugin>
    </model></sdf>""")
    pi=tmp_path/"pi.sdf"
    pi.write_text("""<sdf><model><sensor name="camera" type="camera">
      <topic>camera/image_raw</topic><camera>
        <image><width>640</width><height>480</height><format>R8G8B8</format></image>
      </camera></sensor></model></sdf>""")
    wd=tmp_path/"world.sdf.xacro"
    wd.write_text("""<sdf><world name="default">
      <plugin filename="gz-sim-sensors-system"><render_engine>ogre2</render_engine></plugin>
    </world></sdf>""")
    actor=tmp_path/"walk.dae";actor.write_text("<COLLADA/>")
    return w,pi,wd,actor


def test_actor_moves_on_loop_instead_of_remaining_fixed(tmp_path):
    files=fixture(tmp_path)
    before=[p.read_bytes() for p in files]
    result=make_overlay(*files,tmp_path/"out",cpu_renderer=False)
    assert [p.read_bytes() for p in files]==before
    world=ET.parse(result["world"]).getroot()
    actor=world.find(".//actor[@name='axia_d04_person']")
    assert actor is not None
    assert actor.findtext("script/loop")=="true"
    trajectory=actor.find("script/trajectory")
    assert trajectory.get("type")=="walk"
    waypoints=trajectory.findall("waypoint")
    assert len(waypoints)>=4
    times=[float(x.findtext("time")) for x in waypoints]
    poses=[tuple(map(float,x.findtext("pose").split())) for x in waypoints]
    assert all(b>a for a,b in zip(times,times[1:]))
    assert poses[0]==poses[-1], "a repeating actor should return home"
    assert len({(p[0],p[1]) for p in poses})>=3, "human must traverse camera view"
    assert max(times)<=30.0, "a 5-minute static delay is invisible in a demo"


def test_package_gate_reports_real_visible_progress_and_hold():
    src=(SCRIPTS/"d04_packaged_p1_yolo_gate.py").read_text()
    assert "[D04][" in src
    assert "flush=True" in src
    assert "PERSON" in src
    assert "min(max(a.hold_seconds, 0), 120)" in src
    assert "WSLG_HOST_OPENGL" in src
    assert "HEADLESS_LLVMPIPE" in src
    assert 'env.pop("LIBGL_ALWAYS_SOFTWARE", None)' in src
    assert "create_publisher(" not in src


def test_wsl_script_does_not_hide_10_min_runtime_from_user():
    src=(SCRIPTS/"axia_d04_ros_package_wsl2_once.sh").read_text()
    assert '[D04]' in src
    assert 'tee "$OUT/runtime.log"' in src, "status must be shown live AND preserved"
    assert "AXIA_D04_DEMO_HOLD_S" in src
    assert 'cd "$HOME"' in src
    assert "ros2 action send_goal" not in src
    assert "ros2 topic pub /cmd_vel" not in src


def test_package_launch_exposes_safe_demo_preview_without_motor_paths():
    src=(PKG/"launch/d04_p1_yolo.launch.py").read_text()
    assert 'DeclareLaunchArgument("show_image"' in src
    assert "/yolo/cam0/debug_image" in src
    assert 'package="image_view"' in src
    assert "create_publisher(" not in src
