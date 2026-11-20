"""D08 official ONNX Runtime 1.20.0 immutable upstream source regression.

Previous GitHub .tgz URI returned HTTP 404 in real CI #44202916170.
Do not require that dead URL; fail closed on replacement official NuGet.
L0 only; does not establish C++ inference or Gazebo success.
"""
from pathlib import Path

WF = (Path(__file__).resolve().parents[2] /
      ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml")


def test_exact_official_1200_vendor_asset_is_validated_not_html_or_unpinned():
    s = WF.read_text()
    assert "curl --fail --location" in s
    assert "api.nuget.org/v3-flatcontainer/microsoft.ml.onnxruntime/1.20.0/" in s
    assert "microsoft.ml.onnxruntime.1.20.0.nupkg" in s
    assert "d08_prepare_official_ort_nuget.py" in s
    assert "D08_NUGET_DOWNLOAD_BLOCKED" in s
    assert "D08_NUGET_ASSET_VALIDATION_BLOCKED" in s
    assert "-DONNXRUNTIME_ROOT=$ORT_ROOT" in s
    assert "94d2dd500cb26027ee9c019f4d3a02029ac615cc" in s
    assert "-DONNXRUNTIME_URL=file://$ORT_ARCHIVE" not in s
