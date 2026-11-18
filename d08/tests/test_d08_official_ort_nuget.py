"""RED regression: first upstream ONNX GitHub 1.20.0 tar download HTTP 404.

NuGet validation is L0; never claim real C++ yolo_ros or Gazebo PASS here.
"""
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from d08_prepare_official_ort_nuget import prepare

def fake_package(path, ident="Microsoft.ML.OnnxRuntime", version="1.20.0",
                 lib=True, headers=True):
    root=ET.Element("package")
    meta=ET.SubElement(root, "metadata")
    ET.SubElement(meta, "id").text=ident
    ET.SubElement(meta, "version").text=version
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("x.nuspec",ET.tostring(root))
        if lib:
            data=bytearray(8192)
            data[:6]=b"\x7fELF\x02\x01"
            struct.pack_into("<H",data,18,62)
            z.writestr("runtimes/linux-x64/native/libonnxruntime.so",bytes(data))
        if headers:
            for n in ("onnxruntime_c_api.h","onnxruntime_cxx_api.h",
                      "onnxruntime_cxx_inline.h"):
                z.writestr("build/native/include/"+n,"/* test only */")
        z.writestr("LICENSE.txt", "Copyright (c) Microsoft Corporation " * 5)
        z.writestr("ThirdPartyNotices.txt", "THIRD PARTY SOFTWARE NOTICES " * 5)
    return path

def test_pinned_nuget_contract_l0(tmp_path):
    pkg=fake_package(tmp_path/"official.nupkg")
    root=tmp_path/"out"
    v=prepare(pkg,root)
    assert v["status"]=="D08_OFFICIAL_NUGET_ORT_1200_VALID"
    assert v["version"]=="1.20.0"
    assert len(v["package_sha256"])==64
    assert (root/"include/onnxruntime_cxx_api.h").exists()
    assert (root/"LICENSE").exists() and (root/"ThirdPartyNotices.txt").exists()
    soname=root/"lib/libonnxruntime.so.1"
    assert soname.is_symlink()
    assert soname.readlink().as_posix()=="libonnxruntime.so"
    assert soname.resolve()==(root/"lib/libonnxruntime.so").resolve()
    assert v["elf_loader_alias"]=="libonnxruntime.so.1"
    assert len(v["license_sha256"]) == len(v["notices_sha256"]) == 64
    assert v["ros_or_gazebo_executed"] is False
    assert json.loads((root/"manifest.json").read_text())==v

@pytest.mark.parametrize("version,lib,headers,expected",[
  ("1.20.1",True,True,"PACKAGE_VERSION_MISMATCH"),
  ("1.20.0",False,True,"LINUX_X64_SO_MISSING"),
  ("1.20.0",True,False,"CPP_HEADERS_MISSING"),
])
def test_wrong_arch_headers_or_version_must_fail(tmp_path,version,lib,headers,expected):
    pkg=fake_package(tmp_path/"wrong.nupkg",version=version,lib=lib,headers=headers)
    with pytest.raises(ValueError,match=expected):
        prepare(pkg,tmp_path/"out")

def test_previous_github_tar_404_must_not_be_dressed_as_success():
    wf=(Path(__file__).resolve().parents[2] /
        ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml").read_text()
    assert "api.nuget.org/v3-flatcontainer/microsoft.ml.onnxruntime/1.20.0/" in wf
    assert "-DONNXRUNTIME_ROOT=$ORT_ROOT" in wf
    assert "D08_NUGET_DOWNLOAD_BLOCKED" in wf
    assert "D08_OFFICIAL_NUGET_ORT_1200_VALID" in wf
    assert "94d2dd500cb26027ee9c019f4d3a02029ac615cc" in wf
