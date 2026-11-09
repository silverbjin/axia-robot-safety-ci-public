"""D05 public artifact leak and fail-closed verdict contract."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d05_l2_safe_export import export

def test_whitelisted_safe_evidence_no_private_source_or_weights(tmp_path):
    src=tmp_path/"actual";src.mkdir()
    (src/"private_teacher_solution.py").write_text("DO NOT EXPORT")
    (src/"model.onnx").write_bytes(b"PRIVATE_WEIGHTS")
    (src/"verdict.json").write_text(json.dumps({
        "gate":"G-D05-REAL-RGBD-VALID-TO-UNKNOWN",
        "status":"BLOCKED", "blocker":"NO_VALID_PERSON_RANGE",
        "private_sha":"a"*40, "secret_key":"DO_NOT_EXPORT",
        "valid_status":None,"unknown_after_loss":None,
        "source_counts":{"rgb":1,"depth":1,"detections":0},
        "person_examples":[]}))
    out=tmp_path/"public"
    r=export(src,out)
    assert r["status"]=="BLOCKED"
    assert sorted(p.name for p in out.iterdir())==["SHA256SUMS","safe_verdict.json"]
    payload=(out/"safe_verdict.json").read_text()
    assert "DO_NOT_EXPORT" not in payload
    assert "secret_key" not in payload
    assert r["valid"]["distance_m"] is None
    assert r["goal_sent"] is False and r["certified_estop"] is False
