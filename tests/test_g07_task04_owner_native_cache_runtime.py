"""ROS-free functional proof of pinned G07 Owner native plugin MISS -> HIT.

Mocks only compiler/CMake/dpkg binaries; runs the actual Bash cache block
extracted from the shipped Owner one-shot, and checks per-run SHA custody.
Does not launch Gazebo, change any TTL, or publish any ROS data.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

OWNER=Path(__file__).resolve().parents[1]/"scripts/axia_g07_task04_owner_moving_l3_once.sh"


class NativeCacheRealShellContract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="axia_g07_cache_l0_")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.home=self.root/"home"
        self.home.mkdir()
        self.runtime=self.root/"source"/"runtime"
        self.src=self.runtime/"tools"/"native_s02_public"
        self.src.mkdir(parents=True)
        (self.src/"CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.16)\n")
        (self.src/"s02_witness.cc").write_text("/* fixed witness source */\n")
        self.bin=self.root/"mockbin"
        self.bin.mkdir()
        self.calls=self.root/"calls.log"
        mocks={
            "cmake": """#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${1:-}" == --version ]];then
  echo 'cmake version 3.28.3'
elif [[ "${1:-}" == -S ]];then
  echo CONFIG >> "$MOCK_CALLS"
  mkdir -p "$4"
elif [[ "${1:-}" == --build ]];then
  echo BUILD >> "$MOCK_CALLS"
  printf '%s' "binary_for_${MOCK_ABI}" > "$2/libaxia_g07_s02_ecm_witness.so"
else exit 7
fi
""",
            "dpkg-query": """#!/usr/bin/env bash
printf 'libgz-sim8-dev=%s\\n' "${MOCK_ABI}"
""",
            "c++": """#!/usr/bin/env bash
echo '13.3.0'
"""
        }
        for name,contents in mocks.items():
            p=self.bin/name
            p.write_text(contents)
            p.chmod(0o755)
        full=OWNER.read_text()
        start=full.index('\nNATIVE_BUILD_CACHE_ROOT=')+1
        stop=full.index('\nexport AXIA_G07_TASK03_WITNESS_SHA256=',start)
        self.block=full[start:stop]
        self.assertIn("NATIVE_BUILD_CACHE_KEY",self.block)

    def run_block(self,abi="v1"):
        out=self.root/("run_"+str(len(list(self.root.glob("run_*")))+1))
        out.mkdir()
        env=os.environ.copy()
        env.update(HOME=str(self.home),OUT=str(out),RUNTIME=str(self.runtime),
                   STUDENT_SHA="954fc2f054c50df783bc81c4d0835a6ee6f8645d",
                   MOCK_ABI=abi,MOCK_CALLS=str(self.calls),
                   PATH=str(self.bin)+os.pathsep+os.environ["PATH"])
        script="""set -Eeuo pipefail
hold(){ echo "HOLD:$1" >&2;exit 3; }
startup_mark(){ :; }
""" + self.block
        p=subprocess.run(["bash","-c",script],env=env,
                         capture_output=True,text=True,timeout=12)
        self.assertEqual(p.returncode,0,p.stderr)
        profile=json.loads((out/"native_witness_build_profile.json").read_text())
        self.assertTrue((out/"native_build"/"libaxia_g07_s02_ecm_witness.so").is_file())
        self.assertTrue((out/"native_witness.sha256").is_file())
        self.assertTrue((out/"native_build_config.log").is_file())
        self.assertTrue((out/"native_build.log").is_file())
        self.assertIn("AXIA_G07_NATIVE_WITNESS_CACHE_STATUS=",p.stdout)
        return out,profile

    def count_calls(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def test_cold_then_warm_saves_both_config_and_compile(self):
        a,p1=self.run_block()
        self.assertEqual(p1["cache_status"],"MISS")
        b,p2=self.run_block()
        self.assertEqual(p2["cache_status"],"HIT")
        self.assertEqual(self.count_calls(),["CONFIG","BUILD"])
        self.assertEqual(p1["output_binary_sha256"],p2["output_binary_sha256"])
        self.assertEqual((a/"native_build"/"libaxia_g07_s02_ecm_witness.so").read_bytes(),
                         (b/"native_build"/"libaxia_g07_s02_ecm_witness.so").read_bytes())

    def test_abi_change_invalidates_cache(self):
        self.run_block(abi="gazebo_v1")
        _,p=self.run_block(abi="gazebo_v2")
        self.assertEqual(p["cache_status"],"MISS")
        self.assertEqual(self.count_calls(),["CONFIG","BUILD","CONFIG","BUILD"])

    def test_source_change_invalidates_cache(self):
        self.run_block()
        with (self.src/"s02_witness.cc").open("a") as f:
            f.write("/* changed source */\n")
        _,p=self.run_block()
        self.assertEqual(p["cache_status"],"MISS")
        self.assertEqual(self.count_calls(),["CONFIG","BUILD","CONFIG","BUILD"])

    def test_corrupt_binary_is_rebuilt_not_reused(self):
        _,p=self.run_block()
        cached=self.home/".cache"/"axia"/"g07_task04_native_witness"/p["abi_cache_key"]
        (cached/"libaxia_g07_s02_ecm_witness.so").write_bytes(b"damaged")
        _,next_profile=self.run_block()
        self.assertEqual(next_profile["cache_status"],"MISS")
        self.assertEqual(self.count_calls(),["CONFIG","BUILD","CONFIG","BUILD"])

if __name__=="__main__":
    unittest.main()
