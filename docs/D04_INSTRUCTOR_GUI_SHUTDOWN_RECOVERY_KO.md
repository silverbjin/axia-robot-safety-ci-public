# AXIA D04 강사 시연 — Gazebo 종료 후 YOLO 창 재생성 방지

> ROS 2 Jazzy / Gazebo Harmonic / WSL2 Ubuntu 24.04  
> **SIMULATION ONLY. NO_GOAL / NO_CMD_VEL / NO_FAULT / 인증 E-Stop 검증 없음.**  
> 비공개 P1 정답·강사용 launch 파일은 수정하지 않았다. 종료 소유권 관리는 공개 CI 실행기에만 추가했다. 비공개 CI를 사용하지 않았다.

## 현장 보고와 코드에서 확인한 결함

**보고:** Gazebo 창을 닫자 YOLO 검출 영상 창이 꺼졌다 다시 열리기를 반복, 일반 종료되지 않아 `wsl --shutdown`으로만 중지.

**코드에서 확인:** 기존 `scripts/d04_waffle_pi_rgb_preflight.py::_stop_all()`은 **ROS Launch 부모 PID가 이미 종료되면 `os.killpg`를 건너뛰었다.** 자식인 `image_view`·Gazebo 프로세스가 같은 실행 세션에 살아 있어도 무시될 수 있었다. 또한 `scripts/axia_d04_ros_package_wsl2_once.sh`의 마지막 `xdg-open debug_frame.png`는 종료 후 **실행기 소유가 아닌 이미지 보기 창을 추가로 열었다.**

반복적으로 새 창을 생성하는 *정확한 최초 재시작 주체*는 제공된 현장 로그 없이는 확정할 수 없다. 그러나 위 두 결함은 실제 코드에서 확인됐고, 공개 CI에서 재현·수정했다.

## 변경 내용 — 최소 MVP 범위

1. `scripts/d04_owned_gui_shutdown.py`: ROS Launch가 생성한 **소유 Linux 세션(SID) 전체**를 감시하고, 부모가 이미 종료됐더라도 세션의 살아 있는 PID/PGID에 `SIGINT → SIGTERM → SIGKILL`을 순차 적용한다. 지정된 다른 ROS 세션/일반 사용자 프로그램을 이름으로 무차별 종료하지 않는다.
2. `scripts/d04_packaged_p1_yolo_gate.py`: `GUI_DEMO_HOLD` 동안 최초 관측한 Gazebo GUI PID가 종료 또는 교체되면 남은 유지시간을 기다리지 않고 관리형 Nav2 Shutdown과 소유 GUI 정리로 이동한다. Gazebo GUI PID가 발견되지 않으면 기존 유지시간을 유지하고 GUI 감시는 **미관측**으로 남긴다.
3. 동일 Gate: `Ctrl+C` 또는 `SIGTERM`도 단일 관리형 종료 경로로 처리한다. 사용자가 중단한 실행을 PASS로 올리지 않는다.
4. `scripts/axia_d04_ros_package_wsl2_once.sh`: 종료 후 `xdg-open` 자동 실행을 삭제했다. 저장된 `debug_frame.png`는 증거 파일로 그대로 보존한다.
5. `verdict.json`: `gui_hold`, `shutdown_group_audit`, `shutdown_residual_groups`, `shutdown_quality` 및 `gui_cleanup_contract=D04_OWNED_ROS_SESSION_V1`을 기록한다. 새 그룹 감사에 잔존 PID가 있거나 에스컬레이션이 필요했다면 깨끗한 종료 PASS로 표시하지 않는다.

## WSL2에서 1회 재인수 — 기존 성공 증거 보존

**검증된 공개 강사 실행기 원본:** [fix/d04-owned-gui-shutdown-20261112](https://github.com/silverbjin/axia-robot-safety-ci-public/tree/fix/d04-owned-gui-shutdown-20261112).  
공개 소스 체크아웃의 내부 고정 SHA는 `3668250ac14680b0ea81a67063938374a8c6820f`이다. 외부에서 다운로드하는 원샷 SHA는 최종 공개 CI 검수된 브랜치 커밋을 사용한다.

~~~bash
(
  set -Eeuo pipefail
  SHA='7c911f4d4635e65e860225d2c21adae8cf9d926f'
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT
  curl -fsSL --retry 3 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/scripts/axia_d04_classroom_wsl2_once.sh" \
    -o "$SCRIPT"
  bash -n "$SCRIPT"
  bash "$SCRIPT" --run
)
~~~

이 실행기는 기존 강사 P1·C++ `yolo_ros`·Gazebo 구조와 강사 정답 SHA를 보존한다. 새 증거는 `~/axia_d04_evidence/d04-package-XXXXXXXX/`에 생성하고, 기존 성공 증거를 지우지 않는다. 시연 중 Gazebo 창을 직접 닫는 경우에도 최종 단계에서 소유한 GUI 프로세스를 정리해야 한다.

**정상 종료 기대 문구(모든 줄은 실제 실행 시에만 증거가 된다):**

~~~text
[D04][SHUTDOWN] Requesting Nav2 managed lifecycle Shutdown before SIGINT
[D04][SHUTDOWN] Stopping launch process group
[D04][GUI_SHUTDOWN_AUDIT] {"owned_session_clean": true, ...}
AXIA_D04_PACKAGED_P1_YOLO_MOTION_CLEAN_SHUTDOWN_PASS
D04_PACKAGE_STATUS=PASS_PACKAGED_P1_YOLO_CLEAN_1X
GATE_RC=0
~~~

`[D04][GUI] First Gazebo GUI exit/restart detected`가 출력되면 종료 감시가 창 소멸을 인지한 경우다. `gui_hold.observed_gazebo_gui=false`라면 조기 창 닫기 감시는 **미검증**이며, 깨끗한 최종 종료 여부와 별도 분리해 기록한다.

## 종료 증거만 한번에 확인

~~~bash
(
  set -Eeuo pipefail
  ROOT="$HOME/axia_d04_evidence"
  EVIDENCE="$(find "$ROOT" -mindepth 1 -maxdepth 1 -type d -name 'd04-package-*' \
    -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)"
  test -n "$EVIDENCE"
  python3 - "$EVIDENCE" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1])
p=root/"round-1/live/verdict.json"
v=json.loads(p.read_text())
group=v.get("shutdown_group_audit",{})
print("EVIDENCE=",root)
print("D04_STATUS=",v.get("status"))
print("SHUTDOWN_QUALITY=",v.get("shutdown_quality"))
print("GUI_HOLD=",v.get("gui_hold","UNVERIFIED"))
print("OWNED_GROUP_AUDIT=",group)
print("RESIDUAL_GROUPS=",v.get("shutdown_residual_groups",[]))
print("ESCALATIONS=",v.get("shutdown_escalated",[]))
print("OWNER_SIGNAL=",v.get("owner_stop_signal","NONE"))
print("GUI_CLEAN=",bool(group) and
      all(row.get("residual_count")==0 for row in group.values()))
PY
)
~~~

**인수 수준:** 공개 CI의 모의/실제 Jazzy `image_view` Xvfb 종료 회귀는 PASS. **실제 강사 P1이 포함된 WSL2 Gazebo GUI에서 창 닫기→반복 재열기 없음→완전 종료**는 현장 인수 결과로만 확정한다. 사용자 제공 WSL2 로그에서 최초 경계가 재발하면 그 관측을 공개 CI 회귀에 편입한다.

## 문제가 재발할 때

`wsl --shutdown`으로 전체 환경을 즉시 파괴하기보다 먼저 **새 `EVIDENCE` 및 `package_launch.log`의 최초 `[D04][SHUTDOWN]` 이후 메시지**와 `verdict.json`의 `gui_hold`·`shutdown_group_audit`·`shutdown_quality`를 비교한다. 임의 `pkill -9 -f image_view`, `killall gz`처럼 다른 실습을 종료할 수 있는 명령은 사용하지 않는다.

**학생 실습은 별도 독립 공개 저장소**다. 이 문서/패치는 강사 소유 P1+YOLO 원샷의 종료 문제만 고친다.
