"""AXIA D04 optional P1 vision sidecar launch (ROS 2 Jazzy / Gazebo Harmonic).

No command publisher, custom YOLO detector, goal, fault or P1 source mutation.
The P1 launch is included as-is with only official camera/world file arguments.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from axia_d04_vision_demo.config import build_yolo_config, validate_assets
from axia_d04_vision_demo.overlay import make_overlay


def _cleanup(_context, folder):
    """Only delete files created by D04, after all launched processes exit."""
    if folder.is_dir() and folder.name.startswith("axia_d04_vision_"):
        shutil.rmtree(folder, ignore_errors=True)
    return []


def _launch_setup(context):
    p1 = Path(LaunchConfiguration("p1_launch").perform(context)).expanduser().resolve()
    model = Path(LaunchConfiguration("onnx_model").perform(context)).expanduser().resolve()
    actor = Path(LaunchConfiguration("actor_dae").perform(context)).expanduser().resolve()
    if not p1.is_file() or p1.name != "axia_tb3_p1.launch.py":
        raise ValueError("p1_launch must reference the original AXIA P1 launch Python file")
    validate_assets(model, actor)

    nav = Path(get_package_share_directory("nav2_minimal_tb3_sim"))
    pi_share = Path(get_package_share_directory("turtlebot3_gazebo"))
    temp = Path(tempfile.mkdtemp(prefix="axia_d04_vision_"))
    try:
        overlay = make_overlay(
            nav / "urdf/gz_waffle.sdf.xacro",
            pi_share / "models/turtlebot3_waffle_pi/model.sdf",
            nav / "worlds/tb3_sandbox.sdf.xacro",
            actor,
            temp,
            cpu_renderer=LaunchConfiguration("cpu_renderer").perform(context).lower() == "true",
        )
        params = temp / "yolo_rgb_only.yaml"
        params.write_text(build_yolo_config(model), encoding="utf-8")
    except Exception:
        _cleanup(context, temp)
        raise

    # Reuse private P1's unmodified Nav2->Supervisor->Collision Monitor chain.
    p1_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(p1)),
        launch_arguments={
            "robot_sdf": overlay["robot_sdf"],
            "world": overlay["world"],
            "use_rviz": LaunchConfiguration("use_rviz"),
            "headless": LaunchConfiguration("headless"),
            "use_composition": "false",
            "autostart": "true",
            "allow_fault_injection": "false",
            "use_sim_time": "true",
        }.items(),
    )
    image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        name="axia_d04_rgb_bridge",
        arguments=["/camera/image_raw"],
        output="screen",
    )
    yolo_upstream = Path(get_package_share_directory("yolo_bringup")) / "launch/yolo.launch.py"
    if not yolo_upstream.is_file():
        _cleanup(context, temp)
        raise FileNotFoundError("Pinned yolo_bringup must be built and sourced")
    detector = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(yolo_upstream)),
        launch_arguments={
            "params_file": str(params),
            "namespace": "yolo",
        }.items(),
    )
    preview = Node(
        condition=IfCondition(LaunchConfiguration("show_image")),
        package="image_view",
        executable="image_view",
        name="axia_d04_yolo_preview",
        remappings=[("image", "/yolo/cam0/debug_image")],
        output="screen",
    )
    cleanup = RegisterEventHandler(OnShutdown(on_shutdown=[
        OpaqueFunction(function=_cleanup, args=[temp]),
    ]))
    return [p1_launch, image_bridge, detector, preview, cleanup]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("p1_launch", default_value="",
                              description="Absolute path to the private original AXIA P1 launch file"),
        DeclareLaunchArgument("onnx_model", default_value="",
                              description="Absolute path to approved pinned yolo26n.onnx; not distributed"),
        DeclareLaunchArgument("actor_dae", default_value="",
                              description="Absolute path to pinned Gazebo walk.dae; not distributed"),
        DeclareLaunchArgument("headless", default_value="true",
                              description="Use official Nav2 headless Gazebo server"),
        DeclareLaunchArgument("use_rviz", default_value="false"),
        DeclareLaunchArgument("show_image", default_value="false",
                              description="Optional image_view GUI of real YOLO debug output"),
        DeclareLaunchArgument("cpu_renderer", default_value="false",
                              description="Use OGRE CPU rendering for environments without GPU"),
        OpaqueFunction(function=_launch_setup),
    ])
