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
    shirt=skin=0
    # Centre upper/middle ROI, every other pixel: unlit background gray/green
    # pillars cannot satisfy both categories.
    for y in range(20,330,2):
        for x in range(160,480,2):
            idx=(y*WIDTH+x)*3
            r,g,b=pixels[idx],pixels[idx+1],pixels[idx+2]
            if 20<r<130 and 35<g<170 and g>r*1.1 and 12<b<g*.85:
                shirt+=1
            if 100<=r<235 and r>g+10 and g>b+5 and g>=55 and b>=25:
                skin+=1
    passing=shirt>=150 and skin>=30
    return {'status':'VISUAL_FRAMING_CANDIDATE' if passing
             else 'PERSON_VISIBLE_FRAMING_BLOCKED',
            'sampled_shirt_green_pixels':shirt,
            'sampled_skin_pixels':skin,
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
