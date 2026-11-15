"""Real L2 #43672164632 proved CM source gap 162.678ms when
CPU burner was pinned onto the RESERVED official CM core. RED regression.
Test WSL2-like display load without defeating the protected CM core.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PLAN=ROOT/"d06/live/d06_ci_stress_cpu_topology.py"

def test_adversarial_renderer_load_avoids_cm_verifier_bag_cores():
    assert PLAN.is_file(), "D06_RENDERER_CPU_STRESS_PLAN_MISSING"
    from d06.live.d06_ci_stress_cpu_topology import choose_renderer_load_cpu
    assert choose_renderer_load_cpu([0,1,2,3])==0
    assert choose_renderer_load_cpu([3,4,8,11,15,19,20,22])==3
    assert choose_renderer_load_cpu([2,5,9,17])!=5

def test_no_four_core_cpu_reservation_fails_closed():
    from d06.live.d06_ci_stress_cpu_topology import choose_renderer_load_cpu
    import pytest
    with pytest.raises(ValueError):choose_renderer_load_cpu([0,1,2])
    with pytest.raises(ValueError):choose_renderer_load_cpu([7,7,7,7])

def test_actual_renderer_load_is_bounded_duty_and_keeps_protected_cm_idle():
    from d06.live.d06_ci_stress_cpu_topology import renderer_duty_cycle
    work,sleep=renderer_duty_cycle()
    assert work>0 and sleep>0 and work/(work+sleep)<=0.30
    assert (work+sleep)<=0.060
