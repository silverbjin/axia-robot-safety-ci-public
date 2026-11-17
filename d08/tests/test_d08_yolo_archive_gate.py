"""D08: Regression for actual upstream archive HTML/invalid-tar CI failure.

This only verifies workflow source contract. It is not a YOLO build success.
"""
from pathlib import Path
WF=(Path(__file__).resolve().parents[2]/
    ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml")

def test_real_onnxruntime_release_tar_must_fail_on_http_and_invalid_archive():
    s=WF.read_text()
    assert "curl --fail --location" in s
    assert "onnxruntime-linux-x64-1.20.0.tgz" in s
    assert "tar -tzf" in s
    assert "D08_UPSTREAM_ONNXRUNTIME_DOWNLOAD_INFRA_BLOCKED" in s
    assert "D08_UPSTREAM_ONNXRUNTIME_INVALID_ARCHIVE" in s
    assert "D08_UPSTREAM_ONNXRUNTIME_LIBRARY_MISSING" in s
    assert "-DONNXRUNTIME_URL=file://$ORT_ARCHIVE" in s
    assert "94d2dd500cb26027ee9c019f4d3a02029ac615cc" in s
