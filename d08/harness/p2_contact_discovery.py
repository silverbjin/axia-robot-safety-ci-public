"""Exact Gazebo Harmonic G07 Contact sensor topic resolver.

The SDF <topic> alias is not necessarily published by Harmonic: the actual
sensor can publish under its fully scoped world/model/link/sensor path.
Discovery is evidence of a publisher, NEVER collision-free ground truth.
"""
from __future__ import annotations

ALIAS='/axia_p2_g07/contacts'
SENSOR='/world/default/model/axia_p2_g07_obstacle/link/obstacle_link/sensor/axia_contact/contact'

def resolve_g07_contact_topic(listing:str)->str|None:
    if not isinstance(listing,str) or len(listing)>50000:
        raise ValueError('G07_CONTACT_TOPIC_LIST_INVALID')
    topics=[x.strip() for x in listing.splitlines() if x.strip()]
    if len(topics)!=len(set(topics)):
        raise ValueError('G07_CONTACT_TOPIC_DUPLICATED')
    # Harmonic native path is the actual per-sensor topic observed in
    # Owner evidence; don't trust a visually similar name or /contacts guess.
    if SENSOR in topics:return SENSOR
    if ALIAS in topics:return ALIAS
    return None
