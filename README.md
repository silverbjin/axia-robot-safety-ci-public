# AXIA Robot Safety — Public CI Baseline

This is a standalone **public** CI reference and diagnostic environment. It is NOT the private instructor repository, a live Safety Supervisor implementation, or an acceptance/industrial E-Stop system.

## CI verification ladder

1. **Canary**: `AXIA_PUBLIC_RUNNER_CANARY_OK` must appear in actual GitHub Actions job output.
2. **Python contracts**: Synthetic receiver-wall-time `/scan` interval metrics and SHA256 manifest integrity. Tests do not measure actual Supervisor callback latency.
3. **Jazzy DDS**: Real ROS 2 Jazzy `rclpy` middleware loopback with synthetic `std_msgs/String`; the instructor Supervisor is **not run**.
4. **Official Gazebo**: Official `nav2_bringup` TurtleBot3 **Waffle** headless launch; read-only `/clock`, `/scan`, `/odom` checks and process group shutdown. On this Draft PR, the Gazebo workflow automatically attempts **3** no-motion runs. The **10** run option is restricted to a later workflow dispatch after the workflow exists on the default branch (which requires separate user approval). These checks are not AXIA S01–S05 or G00/G03/G04 acceptance.

All workflows use standard GitHub-hosted `ubuntu-24.04` and require only read access to repository contents. We never clone the instructor private repository or use secrets.

## Running synthetic Python unit tests

```bash
python3 -m pip install pytest==8.3.5
python3 -m pytest -q -ra tests
```

## Safety boundary

The public code does **not** issue `/start`, Nav2 goals, `/cmd_vel`, or fault injections. A clean start or zero velocity command cannot prove physical stopping, and SW Stop is **not** certified E-Stop. Original instructor RTM, actual Goal UUID, terminal Nav2 results, odometry stops, real callback monotonic gap and RTF must be verified separately in private Cloud CI and final local WSL2 acceptance. No public success authorizes `gate_accepted=true`.

**Publication policy:** new standalone history only; never copy private instructor implementation, real bags, answers, or Hidden Tests. Public code is deliberately independent. Merging any `main` branch requires explicit user approval.
