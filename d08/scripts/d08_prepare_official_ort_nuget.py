#!/usr/bin/env python3
"""Validate Microsoft-published ONNX Runtime 1.20.0 NuGet CPU x64 for yolo_ros.

This prepares only upstream-supported -DONNXRUNTIME_ROOT input. No models,
ROS publishers, private teacher code, safety thresholds or native CM changes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import xml.etree.ElementTree as ET
import zipfile

PACKAGE_ID = "Microsoft.ML.OnnxRuntime"
VERSION = "1.20.0"
LIBPATH = "runtimes/linux-x64/native/libonnxruntime.so"
HEADERS = ("onnxruntime_c_api.h", "onnxruntime_cxx_api.h",
           "onnxruntime_cxx_inline.h")


def prepare(package: Path, root: Path) -> dict:
    package, root = Path(package), Path(root)
    if root.exists() or root.is_symlink():
        raise ValueError("D08_NUGET_OUTPUT_EXISTS")
    if not package.is_file() or not zipfile.is_zipfile(package):
        raise ValueError("D08_NUGET_NOT_ZIP")
    with zipfile.ZipFile(package) as zf:
        names = zf.namelist()
        nuspec = [name for name in names if name.lower().endswith(".nuspec")]
        if len(nuspec) != 1:
            raise ValueError("D08_NUGET_METADATA_NOT_UNIQUE")
        meta = ET.fromstring(zf.read(nuspec[0]))
        def field(tag):
            for child in meta.iter():
                if child.tag.rsplit("}", 1)[-1] == tag:
                    return (child.text or "").strip()
            return ""
        if field("id") != PACKAGE_ID or field("version") != VERSION:
            raise ValueError("D08_NUGET_PACKAGE_VERSION_MISMATCH")
        if LIBPATH not in names:
            raise ValueError("D08_NUGET_LINUX_X64_SO_MISSING")
        # Complete, one-directory C++ API header set must match same package.
        matches = {header: [n for n in names if n.endswith("/" + header)]
                   for header in HEADERS}
        if any(len(paths) != 1 for paths in matches.values()):
            raise ValueError("D08_NUGET_CPP_HEADERS_MISSING")
        prefix = matches[HEADERS[0]][0].rsplit("/", 1)[0] + "/"
        if any(not paths[0].startswith(prefix) for paths in matches.values()):
            raise ValueError("D08_NUGET_HEADER_DIRECTORY_MISMATCH")
        lib = zf.read(LIBPATH)
        # Exact ELF64 little-endian x86_64 shared object, never a fake HTML.
        if (len(lib) < 4096 or lib[:5] != b"\x7fELF\x02" or lib[5] != 1
                or struct.unpack_from("<H", lib, 18)[0] != 62):
            raise ValueError("D08_NUGET_SO_NOT_ELF64_X86_64")
        # Read copyright documents from the *same verified Microsoft NuGet*,
        # not from a GitHub raw tag URL which failed HTTP 404 in public CI.
        licenses = [n for n in names if Path(n).name in ("LICENSE.txt", "LICENSE")]
        notices = [n for n in names if Path(n).name == "ThirdPartyNotices.txt"]
        if len(licenses) != 1 or len(notices) != 1:
            raise ValueError("D08_NUGET_LICENSE_NOTICES_MISSING")
        license_bytes, notice_bytes = zf.read(licenses[0]), zf.read(notices[0])
        if len(license_bytes) < 100 or len(notice_bytes) < 100:
            raise ValueError("D08_NUGET_LICENSE_NOTICES_EMPTY")
        headers = sorted(n for n in names if n.startswith(prefix)
                         and not n.endswith("/") and
                         Path(n).suffix in (".h", ".hpp"))
        if len(headers) < 3:
            raise ValueError("D08_NUGET_INCOMPLETE_HEADERS")
        root.mkdir(parents=True)
        (root / "lib").mkdir()
        (root / "include").mkdir()
        (root / "lib/libonnxruntime.so").write_bytes(lib)
        # Verified actual CI #44210297492: upstream yolo_node linked ELF NEEDED
        # libonnxruntime.so.1; NuGet stores only libonnxruntime.so. Keep the
        # immutable Microsoft binary and create its exact runtime SONAME alias.
        (root / "lib/libonnxruntime.so.1").symlink_to("libonnxruntime.so")
        (root / "LICENSE").write_bytes(license_bytes)
        (root / "ThirdPartyNotices.txt").write_bytes(notice_bytes)
        for name in headers:
            rel = name[len(prefix):]
            if not rel or any(t in (".", "..") for t in Path(rel).parts):
                raise ValueError("D08_NUGET_INVALID_HEADER_PATH")
            target = root / "include" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(name) as source, target.open("wb") as dest:
                shutil.copyfileobj(source, dest)
    verdict = {
        "status": "D08_OFFICIAL_NUGET_ORT_1200_VALID",
        "package_id": PACKAGE_ID, "version": VERSION,
        "vendor_source": "api.nuget.org/v3-flatcontainer",
        "package_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
        "lib_sha256": hashlib.sha256(lib).hexdigest(),
        "elf_loader_alias": "libonnxruntime.so.1",
        "license_sha256": hashlib.sha256(license_bytes).hexdigest(),
        "notices_sha256": hashlib.sha256(notice_bytes).hexdigest(),
        "lib_arch": "ELF64 x86_64",
        "header_prefix": prefix,
        "header_count": len(headers),
        "upstream_yolo_code_modified": False,
        "ros_or_gazebo_executed": False
    }
    (root / "manifest.json").write_text(json.dumps(verdict, indent=2) + "\n")
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--root", required=True, type=Path)
    args = ap.parse_args()
    result = prepare(args.package, args.root)
    print(result["status"] + " " + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
