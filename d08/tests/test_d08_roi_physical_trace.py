"""D08 Task01 RED: physical ROI depth must track nearer person and preserve pixels.

L0 fake fixture exercises serialization, never constitutes real Gazebo evidence.
Real #44229304083: slow scan .559762m/ROI .475343m, stop scan .362725m/
ROI .534589m (wrong direction; stop bbox vertical y25..105 only).
"""
import hashlib
from pathlib import Path
from types import SimpleNamespace as S
import struct
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_live_person_range_session import grade_actual_person_stages
from d08_live_person_range import capture_actual_roi_source

def stages():
    return [
        {"stage":"farther","native_ack":True,"roi_status":"VALID",
         "distance_m":.30,"registration_confirmed":True},
        {"stage":"stop","native_ack":True,"roi_status":"VALID",
         "distance_m":.54,"registration_confirmed":True},
        {"stage":"unknown","native_ack":True,"roi_status":"UNKNOWN",
         "distance_m":None,"registration_confirmed":True,
         "reason":"NO_PERSON_CLASS_IN_ACTUAL_YOLO"},
    ]

def test_false_accepted_reverse_roi_trend_is_not_a_two_distance_pass():
    # Absolute delta .24m is large, but direction is physically wrong.
    with pytest.raises(ValueError, match="D08_PERSON_DISTANCE_DIRECTION_INCONSISTENT"):
        grade_actual_person_stages(stages())

def test_capture_true_rgb_bytes_and_16_original_depth_pixels(tmp_path):
    hdr=S(stamp=S(sec=6,nanosec=0),frame_id="axia_d08_rgbd_optical")
    rgb=S(header=hdr,width=4,height=4,encoding="rgb8",step=12,
          data=bytes(range(48)))
    vals=[.3+i*.01 for i in range(16)]
    dp=S(header=hdr,width=4,height=4,encoding="32FC1",step=16,
         data=struct.pack("<16f",*vals),is_bigendian=False)
    bbox={"x1":0,"y1":0,"x2":4,"y2":4,
          "image_width":4,"image_height":4,"confidence":.65}
    report=capture_actual_roi_source(rgb,dp,bbox,tmp_path/"sample.ppm")
    assert report["actual_rgb_frame_sha256"]==hashlib.sha256(bytes(range(48))).hexdigest()
    assert len(report["roi_depth_m"])==16
    assert report["bbox_xyxy"]==[0,0,4,4]
    assert report["rgb_stamp_ns"]==report["depth_stamp_ns"]==6_000_000_000
    assert (tmp_path/"sample.ppm").read_bytes().startswith(b"P6\n4 4\n255\n")
    assert report["roi_valid_count"]==16
