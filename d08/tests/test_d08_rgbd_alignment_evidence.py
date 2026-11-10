"""Actual Owner h14ERUdL: RGB=75, depth=112, no matched pairs 151 times.

Must record WHY; never silently widen the strict <=50ms D05 alignment rule.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_live_readonly_probe import diagnose_rgbd_alignment,select_pair,diagnostic_blocker

def meta(t,frame='axia_d08_rgbd_optical',enc='32FC1'):
    return {'stamp_ns':t,'frame':frame,'width':640,'height':480,'encoding':enc}

def test_real_owner_no_pair_diagnostic_reports_closest_skew_and_headers():
    rgb=[meta(1_000_000_000,enc='rgb8')]
    dep=[meta(1_175_000_000)]
    assert select_pair(rgb,dep) is None
    d=diagnose_rgbd_alignment(rgb,dep)
    assert d['minimum_same_frame_skew_ms']==175.0
    assert d['required_max_skew_ms']==50
    assert d['pair_requirement_relaxed'] is False
    assert d['rgb_last'][0]['encoding']=='rgb8'
    assert d['depth_last'][0]['encoding']=='32FC1'
    assert d['same_frame_candidate_pairs']==1

def test_optical_frame_mismatch_does_not_forge_registering():
    rgb=[meta(1_000_000_000,frame='rgb_optical',enc='rgb8')]
    dep=[meta(1_000_000_000,frame='depth_frame')]
    assert select_pair(rgb,dep) is None
    assert diagnose_rgbd_alignment(rgb,dep)['minimum_same_frame_skew_ms'] is None

def test_actual_same_stamp_still_valid_under_existing_threshold():
    rgb=[meta(4_000_000_000,enc='rgb8')]
    dep=[meta(4_000_000_000)]
    pair=select_pair(rgb,dep)
    assert pair and pair['stamp_skew_ms']==0.0
    assert diagnose_rgbd_alignment(rgb,dep)['minimum_same_frame_skew_ms']==0.0

def test_wrong_depth_encoding_and_image_shape_still_fail_closed():
    rgb=[meta(4_000_000_000,enc='rgb8')]
    wrong=[{**meta(4_000_000_000),'encoding':'16UC1'}]
    assert select_pair(rgb,wrong) is None
    assert diagnose_rgbd_alignment(rgb,wrong)['correct_geometry_encoding_pairs']==0
    wrong2=[{**meta(4_000_000_000),'width':320}]
    assert select_pair(rgb,wrong2) is None

def test_owner_real_0ms_rgbd_with_yolo_tv_is_classified_not_blindly_depth_failed():
    rgb=[meta(105600000000,enc='rgb8')]
    depth=[meta(105600000000)]
    data={'detections_count':86,'yolo_person_count':0}
    assert diagnostic_blocker(rgb,depth,data)=='YOLO_PERSON_CLASS_NOT_DETECTED'
    assert diagnose_rgbd_alignment(rgb,depth)['minimum_same_frame_skew_ms']==0.0
    assert diagnostic_blocker(rgb,[],data)=='RGBD_REGISTERED_PAIR_NOT_FOUND'
    assert diagnostic_blocker(rgb,depth,{'detections_count':0})=='YOLO_DETECTIONS_STREAM_MISSING'
    assert diagnostic_blocker(rgb,depth,{'detections_count':3,'yolo_person_count':1})=='D05_ACTUAL_PERSON_RANGE_NOT_VERIFIED'
