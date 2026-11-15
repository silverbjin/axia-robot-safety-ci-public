"""L2 visual framing check for real, no-Goal Gazebo camera PPM.

This checks whether BOTH green shirt and skin-like face are visible near image
centre, NOT YOLO/person identity, actual D05, or certified safe navigation.
It cannot replace Owner yolo_ros DetectionArray; it catches pants-only imagery.
"""
from pathlib import Path
import json

HEADER=b'P6\n640 480\n255\n'
WIDTH,HEIGHT=640,480

def assess_rgb_ppm(path:Path)->dict:
    raw=Path(path).read_bytes()
    if not raw.startswith(HEADER) or len(raw)!=len(HEADER)+WIDTH*HEIGHT*3:
        raise ValueError('D08_REAL_RGB_IMAGE_EXPECTED_PPM640_480')
    pixels=memoryview(raw)[len(HEADER):]
    shirt=head_skin=pants=0
    # These regions are grounded in the ACTUAL pinned D04 walk.dae
    # (real Gazebo RGB artifact #13781856970). Head is rendered in
    # shadow near RGB(90,75,63), not always >=100 red as before.
    # This only checks visible image framing. NEVER make a YOLO
    # person/3D-depth/safety PASS from colour counts.
    for y in range(60,290,2):
        for x in range(160,480,2):
            idx=(y*WIDTH+x)*3
            r,g,b=pixels[idx],pixels[idx+1],pixels[idx+2]
            if 20<r<130 and 35<g<170 and g>r*1.1 and 12<b<g*.85:
                shirt+=1
    for y in range(25,165,2):
        for x in range(225,415,2):
            idx=(y*WIDTH+x)*3
            r,g,b=pixels[idx],pixels[idx+1],pixels[idx+2]
            if (60<=r<230 and r>g+7 and g>b+4 and
                g>=40 and b>=25 and r-b>=17):
                head_skin+=1
    for y in range(145,430,2):
        for x in range(220,420,2):
            idx=(y*WIDTH+x)*3
            r,g,b=pixels[idx],pixels[idx+1],pixels[idx+2]
            if (8<r<80 and 8<g<100 and b>r*1.4 and b>g*1.35):
                pants+=1
    passing=shirt>=150 and head_skin>=50 and pants>=150
    return {'status':'VISUAL_FRAMING_CANDIDATE' if passing
             else 'PERSON_VISIBLE_FRAMING_BLOCKED',
            'sampled_shirt_green_pixels':shirt,
            'sampled_skin_pixels':head_skin,
            'sampled_head_skin_pixels':head_skin,
            'sampled_navy_pants_pixels':pants,
            'real_ros_image_required':True,
            'yolo_person_detection_verified':False,
            'd05_valid_verified':False,
            'safety_or_collision_certification':False}

if __name__=="__main__":
    import sys
    result=assess_rgb_ppm(Path(sys.argv[1]))
    print('D08_REAL_RGB_VISUAL_FRAME '+json.dumps(result))
    if result['status']!='VISUAL_FRAMING_CANDIDATE':
        raise SystemExit(2)
