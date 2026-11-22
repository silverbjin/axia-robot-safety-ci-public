"""Public, answer-free student scaffold contract. No private Instructor source is loaded."""
import pathlib,sys,xml.etree.ElementTree as ET

PACKAGES=("axia_command_chain_lab","axia_tf_scan_lab","axia_nav2_goal_lab",
          "axia_async_guard_lab","axia_evidence_oracle_lab")

def inspect(root):
    root=pathlib.Path(root)
    assert root.is_dir(), "student lab directory missing"
    assert (root/"tests/test_contracts.py").is_file(), "student public exercises missing"
    for p in PACKAGES:
        base=root/"ros2_ws"/"src"/p
        meta=ET.parse(base/"package.xml").getroot()
        assert meta.findtext("name")==p, "ROS package name mismatch"
        core=(base/p/"core.py").read_text()
        assert "NotImplementedError" in core and "TODO" in core, "TODO removed or answer leaked"
        assert (base/"README_KO.md").is_file(), "lesson guide missing"
        assert "```mermaid" in (base/"README_KO.md").read_text(), "diagram missing"
        assert (base/"setup.py").is_file(), "ament_python setup absent"
        cfg=(base/"setup.cfg").read_text()
        assert "script_dir=$base/lib/"+p in cfg and "install_scripts=$base/lib/"+p in cfg, "ros2 run entrypoint install path missing"
        assert (base/"resource"/p).is_file(), "ament marker absent"
    assert not list(root.rglob("INSTRUCTOR_GUIDE_PRIVATE_KO.md")), "private guide leak"
    assert not list(root.rglob("test_hidden_instructor.py")), "private hidden test leak"
    print("AXIA_VELOG_FIVE_STUDENT_TODO_PACKAGES_AND_DIAGRAMS_PASS")

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: python check_student_contract.py STUDENT_ROOT")
    inspect(sys.argv[1])
