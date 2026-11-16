# AXIA G07 Cycle39 — MVP 범위 축소·정리 실행 계획 (2026-11-17)

## 결정 및 기준
- 사용자 지시: Cycle39를 신규 기능 개발이 아닌 **범위 동결/축소**로 종료한다. GUI-only 교육 시연은 Cycle38 Owner WSLg에서 원본 `EXIT_RC=0` / 사용자 화면 확인. 이를 다시 개발하거나 동일 현장을 반복하지 않는다.
- 공개 저장소 `silverbjin/axia-robot-safety-ci-public`, 현재 Draft PR #136, 기준 브랜치 `fix/g07-cycle38-d07-wslg-gpu-xcb-capture-20261117`. 강사 비공개 정답·학생 패키지·official Nav2·CM·Guard·Supervisor는 변경 금지. main 병합은 Owner 승인 대기.
- 원래 CM 120ms margin은 Release HOLD. 128.644215ms 원본 [CI #43898345608](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43898345608)는 원래 150ms TTL 위반의 증명이 아니다.
- Cycle39 신규 Gazebo P1/P2 L2 미인수. 독립 센서 정합/타이밍 검증을 이번 MVP의 추가 합격조건으로 만들지 않는다.

## 단계별 계획: RED → GREEN → REFACTOR → REVIEW → COMMIT
1. **기준/RED:** 고정된 C38 `c4dca31b210d28037116e49fe39d8d0b5aebdc34`의 표시/각도 문제를 두 개 핵심 단위 회귀로 재현한다. 이전 Cycle39 RED→GREEN [Run #43916055772](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43916055772)의 실제 RED 2 failures + 5 errors, GREEN 9/9을 이력으로 보존한다. 새 RED replay는 표시/전방각도만 검사한다.
2. **GREEN 최소 유지:** `d06/rviz/d06_safety_bubble.rviz`의 TF 화살표 숨김, 카메라 조정만 유지한다. `d06/live/d06_readonly_monitor.py`의 전방 각도 `atan2(sin,cos)` wrap만 남기고 Cycle39에서 추가한 Scan header/clock diagnostic 필드는 삭제(원래 관찰기/안전 publisher 변경 금지).
3. **REFACTOR 범위 제거:** `d06/live/g07_cycle39_scan_geometry.py`, `d06/live/g07_cycle39_scan_timing.py`, `.github/workflows/axia-g07-cycle39-gazebo-scan-snapshot-l2.yml`를 Draft PR에서 제거한다. `d06/tests/test_g07_cycle39_display_scan_timing.py`는 표시+각도+read-only 계약만 남기며, `.github/workflows/axia-g07-cycle39-display-scan-l0.yml`는 단일 공개 L0 RED→GREEN만 실행한다. **새 주행 CI/L2 생성 금지.**
4. **REVIEW 및 공개 CI:** PR 실제 diff에서 안전 제어 관련 파일 변경 0, 새로운 Goal/vel publisher 0, 실험적인 CI L2 변경 0을 확인한다. 공개 CI L0 PASS의 정확한 Run ID/테스트 수/소스 SHA를 확인하고 출력 원문을 보고서에 기록한다. PASS 전 Owner 배포/주행 금지.
5. **RELEASE CI 임시 워크플로 청소:** `release/p2-g06-cm-ttl-20261110`에 Cycle39용으로 추가한 동일 파일만 삭제하여 기존 성공 CI 워크플로를 훼손하지 않는다. 해당 브랜치의 Owner 시연·실제 L2는 재실행하지 않는다.
6. **최종 보고/종료:** 수행 결과, 실제 RED/GREEN, 파일 경로, 정확한 커밋/브랜치/PR, 검증 수준과 남은 별도 G07 Moving Goal/CM 120ms HOLD를 기록한다. PR은 Draft/Open 유지, main 자동 병합 금지.

## 완료 정의
- Cycle39 Draft PR은 **표시 설정+교육용 전방각도 수정+회귀 테스트+문서**만 포함한다.
- 0/2π 교육용 거리 계산과 화면 표시 정적 검증에 대한 공개 CI GREEN을 확보한다.
- 최초 성공 Cycle38 현장 증거를 재사용하고 `AXIA_MVP_DEMO_ACCEPTED=HOLD`, `CM_120MS_RELEASE=HOLD`, `CERTIFIED_ESTOP=false`, `OWNER_MOVING_L3=NOT_RUN`을 유지한다.
- 새 P1/P2 진단 라이브러리, 전용 L2, Owner 현장 재실행이나 안전 인증 개발을 확대하지 않는다.

## 검증 명령 (CI)
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s d06/tests -p 'test_g07_cycle39_display_scan_timing.py' -v
python3 -m py_compile d06/live/d06_readonly_monitor.py
```
위 명령은 ROS/Gazebo 실측 검증이 아닌 L0이며, 실제 Gazebo/Moving Goal 성공을 뜻하지 않는다.
