"""RED: Owner jlZsbcmp CI showed only navy pants, no shirt or head.
This is strictly a simulated-camera visual framing regression, not YOLO.
"""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_visible_person_frame import HEADER,assess_rgb_ppm

def frame(path,person=False):
    width,height=640,480
    rgb=bytearray(bytes([205,205,205])*(width*height))
    if person:
        for y in range(90,230):
            for x in range(230,400):
                at=(y*width+x)*3
                rgb[at:at+3]=bytes([45,90,37]) # shirt in centre
        for y in range(35,87):
            for x in range(285,350):
                at=(y*width+x)*3
                rgb[at:at+3]=bytes([172,117,86]) # visible face
        for y in range(230,380):
            for x in range(260,365):
                at=(y*width+x)*3
                rgb[at:at+3]=bytes([21,28,60]) # visible navy legs
    path.write_bytes(HEADER+bytes(rgb))
    return path

def test_only_pants_fails_visual_framing(tmp_path):
    f=frame(tmp_path/'pants.ppm')
    result=assess_rgb_ppm(f)
    assert result['status']=='PERSON_VISIBLE_FRAMING_BLOCKED'
    assert result['sampled_shirt_green_pixels']==0
    assert result['sampled_skin_pixels']==0
    assert not result['yolo_person_detection_verified']

def test_actual_view_with_shirt_and_head_is_candidate_not_yolo_pass(tmp_path):
    result=assess_rgb_ppm(frame(tmp_path/'human.ppm',True))
    assert result['status']=='VISUAL_FRAMING_CANDIDATE'
    assert result['sampled_shirt_green_pixels']>=150
    assert result['sampled_skin_pixels']>=30
    assert result['sampled_navy_pants_pixels']>=150
    assert result['yolo_person_detection_verified'] is False
    assert result['d05_valid_verified'] is False

def test_actual_shaded_d04_head_pixels_are_visible_not_a_false_negative(tmp_path):
    # Reproduce verified Gazebo RGB from run #42853632220: upper head
    # pixels are about RGB(90,75,63), not the old >=100 skin cutoff.
    width,height=640,480
    rgb=bytearray(bytes([218,218,218])*(width*height))
    for y in range(100,175):
        for x in range(220,420):
            at=(y*width+x)*3
            rgb[at:at+3]=bytes([29,51,25])
    for y in range(60,105):
        for x in range(280,340):
            at=(y*width+x)*3
            rgb[at:at+3]=bytes([90,75,63])
    for y in range(176,370):
        for x in range(260,360):
            at=(y*width+x)*3
            rgb[at:at+3]=bytes([21,28,60])
    p=tmp_path/'actual_d04_shaded.ppm'
    p.write_bytes(HEADER+bytes(rgb))
    r=assess_rgb_ppm(p)
    assert r['status']=='VISUAL_FRAMING_CANDIDATE',r
    assert r['sampled_head_skin_pixels']>=50
    assert r['sampled_navy_pants_pixels']>=150
    assert r['yolo_person_detection_verified'] is False


def test_nonstandard_ppm_rejected(tmp_path):
    file=tmp_path/'invalid.ppm'
    file.write_bytes(b'P6\\n640 480\\n255\\n' + b'0'*(640*480*3))
    with pytest.raises(ValueError,match='PPM'):assess_rgb_ppm(file)
