"""D08 Task01 L0 only: synthetic byte fixtures for strict public read-only status."""
import sys
import struct
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_public_person_range import assess_public_person_range

SDF="a"*64
BB={"x1":2,"y1":2,"x2":10,"y2":8,"image_width":12,"image_height":10}
def header(ns=2_000_000_000, frame="axia_d08_rgbd_optical"):
    return NS(stamp=NS(sec=ns//1_000_000_000,nanosec=ns%1_000_000_000),frame_id=frame)
def msgs(distance, stamp_ns=2_000_000_000):
    hd=header(stamp_ns)
    rgb=NS(header=hd,width=12,height=10,encoding="rgb8")
    raw=struct.pack("<f",distance)*120
    dep=NS(header=hd,width=12,height=10,step=48,
           is_bigendian=False,encoding="32FC1",data=raw)
    return rgb,dep
def check(distance=1.5,**kw):
    rgb,depth=msgs(distance)
    return assess_public_person_range(
      rgb,depth,kw.get("det_stamp_ns",2_000_000_000),
      kw.get("det_frame","axia_d08_rgbd_optical"),BB,
      kw.get("received",{"rgb":10.1,"depth":10.1,"detection":10.1}),
      10.2,kw.get("sdf",SDF))
def test_two_distinct_l0_fixtures_not_a_physical_gazebo_acceptance():
    a,b=check(0.65),check(1.5)
    assert a["status"]==b["status"]=="VALID"
    assert a["distance_m"]==0.65 and b["distance_m"]==1.5
    assert a["control_published"] is False
def test_unknown_on_stale_or_header_skew_or_frame_or_no_registration():
    assert check(received={"rgb":9.0,"depth":10.1,"detection":10.1})["reason"]=="INPUT_STALE_OR_FUTURE"
    assert check(det_stamp_ns=2_060_000_000)["reason"]=="TRIAD_STAMP_SKEW"
    assert check(det_frame="other")["reason"]=="OPTICAL_FRAME_MISMATCH"
    assert check(sdf="")["reason"]=="REGISTRATION_SDF_EVIDENCE_MISSING"
def test_unknown_on_invalid_real_pixel_samples():
    assert check(float("nan"))["reason"]=="INSUFFICIENT_VALID_DEPTH_PIXELS"
