"""Pure evidence parser for actual Gazebo Harmonic gz.msgs.Contacts text.

This is NOT a safety controller, collision-free oracle, or a substitute for
owner moving-Goal raw evidence. One non-robot positive calibration only.
"""
from __future__ import annotations
import re

COLLISION_PAIR=re.compile(
    r'collision1\s*\{\s*id:\s*\d+\s*name:\s*"([^"]+)"\s*\}'
    r'\s*collision2\s*\{\s*id:\s*\d+\s*name:\s*"([^"]+)"\s*\}',
    re.DOTALL,
)
PHYSICAL='axia_p2_g07_obstacle::obstacle_link::obstacle_collision'
PROBE='axia_d08_contact_calibrator::calibrator_link::calibrator_collision'

def count_nonrobot_positive_contacts(native_output:str)->int:
    if not isinstance(native_output,str):
        raise TypeError('native_output must be Gazebo Contact text')
    return sum(set(names)=={PHYSICAL,PROBE}
               for names in COLLISION_PAIR.findall(native_output))
