"""D04 user WSL2 errors -> public CI regressions, WITHOUT requiring ROS/Gazebo/weights.

RED: the runner below does not exist in the baseline branch. The first failure
must be "missing course runner", not mock ROS/Yolo.
GREEN: run from arbitrary cwd, diagnose missing assets/ultralytics/source before
attempted private path or model execution, and run an injected demo path.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "axia_d04_course_once.sh"


def run(*args: str, cwd: Path, env: dict | None = None):
    e = os.environ.copy()
    e.update(env or {})
    return subprocess.run(
        ["bash", str(RUNNER), *args],
        cwd=cwd,
        env=e,
        text=True,
        capture_output=True,
        timeout=12,
    )


def test_runner_exists_and_has_safe_syntax():
    assert RUNNER.is_file(), "RED: course runner absent; README shell commands fail from ~"
    r = subprocess.run(["bash", "-n", str(RUNNER)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_doctor_from_home_reports_all_preflight_faults(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    e = {
        "HOME": str(home),
        "AXIA_D04_PYTHON": sys.executable,
    }
    r = run(
        "--doctor",
        "--instructor", str(home / "instructor"),
        "--model", str(home / "no-model.pt"),
        "--image", str(home / "no-image.jpg"),
        cwd=home,
        env=e,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "D04_MODEL_MISSING" in r.stdout
    assert "D04_IMAGE_MISSING" in r.stdout
    assert "D04_INSTRUCTOR_SCRIPT_MISSING" in r.stdout
    assert "D04_ULTRALYTICS_MISSING" in r.stdout
    assert "can't open file" not in (r.stdout + r.stderr)
    assert "ModuleNotFoundError" not in (r.stdout + r.stderr)


def test_image_refuses_unsafe_missing_dependencies_before_execution(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    r = run(
        "--image",
        "--instructor", str(home / "instructor"),
        "--model", str(home / "missing.pt"),
        "--image", str(home / "missing.jpg"),
        cwd=home,
        env={"HOME": str(home), "AXIA_D04_PYTHON": sys.executable},
    )
    assert r.returncode == 2
    assert "D04_IMAGE_PREFLIGHT_BLOCKED" in r.stdout
    assert "can't open file" not in r.stderr


def test_image_runs_absolute_instructor_script_from_arbitrary_cwd(tmp_path):
    # Public test uses an injected stand-in module and stand-in instructor script.
    # Never treats it as an actual YOLO model or private reference verification.
    home = tmp_path / "home"
    home.mkdir()
    teacher = tmp_path / "teacher"
    src = teacher / "training" / "block_B" / "instructor" / "yolo_single_image_demo.py"
    src.parent.mkdir(parents=True)
    src.write_text(
        "from pathlib import Path\n"
        "import argparse\n"
        "p=argparse.ArgumentParser();p.add_argument('--model');"
        "p.add_argument('--image');p.add_argument('--out');a=p.parse_args()\n"
        "assert Path(a.model).is_file() and Path(a.image).is_file()\n"
        "out=Path(a.out);out.mkdir(parents=True,exist_ok=False)\n"
        "(out/'detections.csv').write_text('frame_id,category\\nf001,person\\n')\n"
        "(out/'run_manifest.json').write_text('{\"ros_verified\":false,\"gazebo_verified\":false}')\n"
        "print('LOCAL_YOLO_CPU_ONLY: 1 persons; output='+str(out))\n"
    )
    lib = tmp_path / "lib"
    lib.mkdir()
    (lib / "ultralytics.py").write_text("# STUB: only package import preflight\n")
    model = tmp_path / "model.pt"
    image = tmp_path / "person.jpg"
    model.write_bytes(b"stub model, not YOLO weights")
    image.write_bytes(b"stub image, not a real photograph")
    out = tmp_path / "results" / "new"
    r = run(
        "--image", "--instructor", str(teacher),
        "--model", str(model), "--image", str(image), "--out", str(out),
        cwd=home,
        env={"HOME": str(home), "AXIA_D04_PYTHON": sys.executable,
             "PYTHONPATH": str(lib)},
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "D04_IMAGE_SCRIPT_PASS_LEVEL=STUB_PUBLIC_CONTRACT" in r.stdout
    assert (out / "detections.csv").exists()
    assert (out / "run_manifest.json").exists()
