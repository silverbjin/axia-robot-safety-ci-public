#!/usr/bin/env python3
"""Read-only COLLADA geometry metadata for pinned D04 walk.dae.

DIAGNOSTIC ONLY: mesh render transforms may add scene matrices/bone skins.
Do not claim Gazebo ground contact from source vertices alone.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

PIN = "49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e"

def inspect(path: Path) -> dict:
    path=Path(path)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if sha!=PIN:
        raise ValueError("UNVERIFIED_D04_MESH_SHA")
    root=ET.parse(path).getroot()
    ns={"c":"http://www.collada.org/2005/11/COLLADASchema"}
    unit=root.find(".//c:asset/c:unit",ns)
    axis=root.findtext(".//c:asset/c:up_axis",default="UNKNOWN",namespaces=ns)
    results=[]
    for geom in root.findall(".//c:library_geometries/c:geometry",ns):
        mesh=geom.find("c:mesh",ns)
        if mesh is None:continue
        verts=mesh.find("c:vertices",ns)
        pos_id=None
        if verts is not None:
            for inp in verts.findall("c:input",ns):
                if inp.attrib.get("semantic")=="POSITION":pos_id=inp.attrib.get("source","").lstrip("#")
        if not pos_id:continue
        sources={x.attrib.get("id"):x for x in mesh.findall("c:source",ns)}
        src=sources.get(pos_id)
        if src is None:continue
        arr=src.find("c:float_array",ns)
        if arr is None or not arr.text:continue
        acc=src.find(".//c:accessor",ns)
        stride=int(acc.get("stride",3)) if acc is not None else 3
        vals=[float(v) for v in arr.text.split()]
        if stride<3 or len(vals)<3:continue
        points=[vals[i:i+3] for i in range(0,len(vals)-stride+1,stride)]
        lower=[round(min(p[i] for p in points),6) for i in range(3)]
        upper=[round(max(p[i] for p in points),6) for i in range(3)]
        results.append({"geometry":geom.get("name",geom.get("id")),
                        "count":len(points),"lower_xyz":lower,"upper_xyz":upper})
    return {"sha256":sha,"up_axis":axis,"unit_meter":unit.get("meter") if unit is not None else None,
            "geometry":results,"note":"source vertices only; Gazebo runtime render needs separate verification"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mesh",type=Path)
    print("D08_WALK_DAE_SOURCE_BOUNDS="+json.dumps(inspect(p.parse_args().mesh)))
