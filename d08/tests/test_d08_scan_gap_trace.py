"""First failure regression from actual #44200740416: 519.095ms scan gap."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import first_scan_receive_gap

def test_real_fail_boundary_first_receive_gap_not_hidden():
    samples=[(100.0,1_000_000_000),
             (100.10,1_100_000_000),
             (100.619095,1_200_000_000)]
    e=first_scan_receive_gap(samples)
    assert e["sample_index"]==2
    assert e["receive_gap_sec"]==0.519095
    assert e["header_sim_gap_sec"]==0.1
    assert e["not_proven_source_vs_transport"] is True
    assert e["publisher_rmw_gap_measured"] is False

def test_near_boundary_is_not_relaxed_or_faked():
    assert first_scan_receive_gap([
      (1.0,100_000_000),(1.499,200_000_000)]) is None
    assert first_scan_receive_gap([
      (1.0,100_000_000),(1.5,200_000_000)])["limit_sec"]==0.5
