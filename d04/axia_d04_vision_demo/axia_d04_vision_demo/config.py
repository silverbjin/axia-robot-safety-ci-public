"""Pinned upstream yolo_ros v5 CPU 2D detection+debug configuration; no motor output."""
from __future__ import annotations

import hashlib
from pathlib import Path

PINNED_YOLO_SHA = "94d2dd500cb26027ee9c019f4d3a02029ac615cc"
PINNED_ONNX_SHA256 = "4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf"
PINNED_ACTOR_SHA256 = "49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e"


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_assets(model: Path, actor: Path) -> dict:
    """Fail closed on missing/changed licensed runtime-only external resources."""
    model, actor = Path(model), Path(actor)
    if not model.is_file() or model.suffix.lower() != ".onnx":
        raise ValueError("ONNX model missing or invalid extension")
    if not actor.is_file() or actor.suffix.lower() != ".dae":
        raise ValueError("Gazebo human actor DAE missing")
    if _sha(model) != PINNED_ONNX_SHA256:
        raise ValueError("ONNX SHA256 mismatch with verified pretrained model")
    if _sha(actor) != PINNED_ACTOR_SHA256:
        raise ValueError("Actor SHA256 mismatch with verified D04 resource")
    return {"onnx_sha256": PINNED_ONNX_SHA256, "actor_sha256": PINNED_ACTOR_SHA256}


def build_yolo_config(model: Path) -> str:
    """Use yolo_ros's actual C++ DetectionPlugin and DebugPlugin unmodified."""
    model = Path(model)
    if model.suffix.lower() != ".onnx":
        raise ValueError("Only local ONNX model is allowed")
    # Quotes and backslashes in path must never be interpolated into YAML.
    absolute = str(model.expanduser().resolve())
    if any(c in absolute for c in ('"', "\n", "\r", "\\", "\0")):
        raise ValueError("Unsupported model pathname")
    return f"""/yolo/yolo_node:
  ros__parameters:
    use_sim_time: true
    plugins: ["detection", "debug"]
    cameras: ["cam0"]
    cam0:
      rgb_topic: /camera/image_raw
      image_reliability: 2
    detection:
      plugin: yolo_ros/DetectionPlugin
      cameras: ["cam0"]
      model_path: "{absolute}"
      model_repo: ""
      model_filename: ""
      model_type: auto
      provider: cpu
      threshold: 0.15
      iou: 0.45
      n_threads: 2
      max_fps: 5
    debug:
      plugin: yolo_ros/DebugPlugin
      cameras: ["cam0"]
"""
