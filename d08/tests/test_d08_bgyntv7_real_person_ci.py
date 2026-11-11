"""BgYnTVv7: field RGB-D was valid but all 52 YOLO detections were umbrella.

PUBLIC sanitized oracle only. The original raw archive and teacher D05 code
must never be committed to this repository. These tests do not claim real YOLO,
a moving Goal, D05 range, or safety certification.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT/'.github/workflows/d08-human-physical-contact-ci.yml'
FIELD={
    'rgb_count':72,
    'depth_count':127,
    'registered_pair_valid':True,
    'candidate_pairs':25,
    'minimum_skew_ms':0.0,
    'detections_count':52,
    'class_counts':{'umbrella':52},
    'yolo_person_count':0,
    'd05_valid_count':0,
    'goal_sent':False,
    'status':'BLOCKED_D08_SENSOR_L2',
}

def test_bgyntv7_genuine_field_witness_remains_negative():
    f=FIELD
    assert f['rgb_count']>0 and f['depth_count']>0
    assert f['registered_pair_valid'] and f['candidate_pairs']>=1
    assert f['minimum_skew_ms']<=50
    assert f['detections_count']==f['class_counts']['umbrella']==52
    assert f['yolo_person_count']==0 and f['d05_valid_count']==0
    assert not f['goal_sent'] and f['status']=='BLOCKED_D08_SENSOR_L2'

def test_public_real_gazebo_ci_exercises_actual_pinned_onnx_on_rgb():
    """RED against current CI: a pixel framing canary is NOT a person detector.

    Must call an ONNX runtime probe on actual Gazebo RGB captured by the
    existing L2 test; the command must fail if person class 0 is not present.
    This is separate from the private ROS yolo_ros + D05 Owner gate.
    """
    workflow=WORKFLOW.read_text()
    assert re.search(r'python[0-9.]*\s+d08/scripts/d08_actual_rgb_onnx_probe\.py',workflow), (
        'BGYNTV7_CI_ORACLE_GAP_REAL_YOLO_MODEL_NOT_EXECUTED')
    assert 'D08_ACTUAL_ONNX_PERSON_FRAME_L2_PASS' in workflow, (
        'BGYNTV7_CI_PERSON_POSITIVE_VERDICT_MISSING')
    assert '4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf' in workflow, (
        'BGYNTV7_CI_ONNX_MODEL_SHA_NOT_PINNED')
