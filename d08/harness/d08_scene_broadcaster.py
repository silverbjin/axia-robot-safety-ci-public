"""D08 GUI SceneBroadcaster: server-side proof, not a WSLg pixel PASS.

Official Nav2 tb3_simulation_launch.py uses an SDF/Xacro headless arg to
conditionally include SceneBroadcaster. D08 expands world BEFORE official
Nav2 consumes it, so D08-generated final SDF MUST include exactly one.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PLUGIN_NAME='gz::sim::systems::SceneBroadcaster'
PLUGIN_FILE='gz-sim-scene-broadcaster-system'

def validate_d08_scene_world(world_sdf:Path)->dict:
    root=ET.parse(world_sdf).getroot()
    worlds=root.findall('./world')
    if len(worlds)!=1 or worlds[0].get('name')!='default':
        raise ValueError('D08_GAZEBO_SCENE_WORLD_NOT_DEFAULT')
    plugins=[x for x in worlds[0].findall('./plugin')
             if x.get('name')==PLUGIN_NAME or x.get('filename')==PLUGIN_FILE]
    if not plugins:raise ValueError('D08_GAZEBO_SCENE_BROADCASTER_MISSING')
    if len(plugins)>1:raise ValueError('D08_GAZEBO_SCENE_BROADCASTER_DUPLICATE')
    if plugins[0].get('name')!=PLUGIN_NAME or plugins[0].get('filename')!=PLUGIN_FILE:
        raise ValueError('D08_GAZEBO_SCENE_BROADCASTER_NAME_FILENAME_MISMATCH')
    return {'status':'D08_RENDERED_SCENE_BROADCASTER_PRESENT_L0',
            'scene_broadcaster_count':1,'world_name':'default',
            'scene_service_observed':False,'gui_pixels_verified':False}

def validate_native_scene_reply(reply:str)->dict:
    """Require native gz.msgs.Scene robot+physical-human model proof.

    The Gazebo server returns this scene; CI must never create fake services.
    """
    names=set(re.findall(r'\bname:\s*"([^"]+)"',reply))
    fixture='axia_p2_g07_obstacle' in names
    robot='axia_d08_ci_waffle' in names
    if 'model {' not in reply or not fixture or not robot:
        raise ValueError('D08_GAZEBO_NATIVE_SCENE_MODELS_MISSING')
    return {'status':'D08_REAL_GAZEBO_SCENE_BROADCASTER_L2_PASS',
            'native_scene_service_verified':True,
            'robot_model_in_native_scene':robot,
            'physical_person_model_in_native_scene':fixture,
            'gui_pixels_verified':False,'certified_estop':False}
