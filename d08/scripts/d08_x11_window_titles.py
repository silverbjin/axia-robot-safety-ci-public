#!/usr/bin/env python3
"""D08 real X11 viewable-window witness; substitute missing xwininfo only.

Ubuntu24 host Xvfb and libX11 used in CI; never changes or fakes a
Gazebo/ROS/Goal process. Fail closed if actual mapped GUI windows absent.
"""
from __future__ import annotations
import ctypes as C
import ctypes.util
import sys


class XWindowAttributes(C.Structure):
    _fields_ = [
        ("x", C.c_int), ("y", C.c_int), ("width", C.c_int),
        ("height", C.c_int), ("border_width", C.c_int),
        ("depth", C.c_int), ("visual", C.c_void_p),
        ("root", C.c_ulong), ("class_", C.c_int),
        ("bit_gravity", C.c_int), ("win_gravity", C.c_int),
        ("backing_store", C.c_int), ("backing_planes", C.c_ulong),
        ("backing_pixel", C.c_ulong), ("save_under", C.c_int),
        ("colormap", C.c_ulong), ("map_installed", C.c_int),
        ("map_state", C.c_int), ("all_event_masks", C.c_long),
        ("your_event_mask", C.c_long),
        ("do_not_propagate_mask", C.c_long),
        ("override_redirect", C.c_int), ("screen", C.c_void_p),
    ]


def classify_titles(titles):
    if not isinstance(titles,list) or any(not isinstance(t,str) for t in titles):
        raise ValueError("D08_X11_TITLES_INVALID")
    names=[s.casefold() for s in titles]
    return {"rviz":any("rviz" in s for s in names),
            "gazebo":any("gazebo" in s for s in names)}


def scan_real_x11(max_windows=3000,max_depth=8):
    lib=C.CDLL(C.util.find_library("X11") or "libX11.so.6")
    lib.XOpenDisplay.argtypes=[C.c_char_p]
    lib.XOpenDisplay.restype=C.c_void_p
    lib.XDefaultRootWindow.argtypes=[C.c_void_p]
    lib.XDefaultRootWindow.restype=C.c_ulong
    lib.XQueryTree.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong),
        C.POINTER(C.c_ulong),C.POINTER(C.POINTER(C.c_ulong)),C.POINTER(C.c_uint)]
    lib.XQueryTree.restype=C.c_int
    lib.XFetchName.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(C.c_char_p)]
    lib.XFetchName.restype=C.c_int
    lib.XGetWindowAttributes.argtypes=[C.c_void_p,C.c_ulong,C.POINTER(XWindowAttributes)]
    lib.XGetWindowAttributes.restype=C.c_int
    lib.XFree.argtypes=[C.c_void_p]
    lib.XCloseDisplay.argtypes=[C.c_void_p]
    lib.XCloseDisplay.restype=C.c_int
    display=lib.XOpenDisplay(None)
    if not display:
        raise RuntimeError("D08_X11_REAL_DISPLAY_MISSING")
    titles=[]
    queue=[(lib.XDefaultRootWindow(display),0)]
    count=0
    try:
        while queue and count<max_windows:
            window,depth=queue.pop(0)
            count+=1
            name=C.c_char_p()
            if lib.XFetchName(display,window,C.byref(name)) and name.value:
                value=name.value.decode("utf-8","replace")[:120]
                attrs=XWindowAttributes()
                if (lib.XGetWindowAttributes(display,window,C.byref(attrs))
                        and attrs.map_state==2):
                    titles.append(value)
            if name:
                lib.XFree(C.cast(name,C.c_void_p))
            if depth>=max_depth:
                continue
            root=C.c_ulong();parent=C.c_ulong()
            children=C.POINTER(C.c_ulong)();number=C.c_uint()
            if lib.XQueryTree(display,window,C.byref(root),C.byref(parent),
                              C.byref(children),C.byref(number)):
                for index in range(min(number.value,max_windows-count)):
                    queue.append((children[index],depth+1))
            if children:
                lib.XFree(C.cast(children,C.c_void_p))
    finally:
        lib.XCloseDisplay(display)
    return titles,count


def main():
    try:
        titles,count=scan_real_x11()
        flags=classify_titles(titles)
    except (OSError,RuntimeError,ValueError) as exc:
        print("D08_X11_WINDOW_READONLY_HOLD "+type(exc).__name__,file=sys.stderr)
        return 2
    if flags["rviz"]:
        print("RViz viewable X11 window verified")
    if flags["gazebo"]:
        print("Gazebo viewable X11 window verified")
    if flags["rviz"] and flags["gazebo"]:
        print("D08_X11_TWO_ACTUAL_GUI_WINDOWS_VIEWABLE_PASS")
        return 0
    print("D08_X11_GUI_WINDOWS_NOT_BOTH_VIEWABLE visited="+str(count),file=sys.stderr)
    return 2


if __name__=="__main__":
    raise SystemExit(main())
