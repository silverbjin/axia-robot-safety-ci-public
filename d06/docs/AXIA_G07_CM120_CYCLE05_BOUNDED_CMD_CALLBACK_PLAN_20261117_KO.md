# AXIA G07 Cycle05 — 실제 최초 CM RMW 공백의 cmd_vel 콜백 실행시간 진단

## 목적: 새로운 기능이 아니라 원인 분리
- Cycle04 actual configured CM metadata /cmd_vel_supervised C++ callback handle 한 개 실증. [Run #43994237080](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43994237080), NO_GOAL RED/ GREEN4+L1 성공, 최초 Run #43993776141 종료 증거 missing도 교육용으로 보존.
- C37 Moving Goal #43898345608 CM RMW max128.644ms, Cycle01 #43981875149 CM133.659ms >120ms release. Owner Guard CM age158.008ms>150ms hard violation은 별개.
- Cycle03 NO_GOAL clock/odom/TF 최대 wall 공백 교집합333.601ms, Moving 동일 구간이 아님.
- **이번 Cycle05**: 최초 post-Goal CM RMW source gap 120ms+ 한 쌍의 Observer MONOTONIC 시간창과, 정확한 CM vpid와 공식 /cmd_vel_supervised subscription callback handle의 `callback_start/end` 연속쌍을 대조한다. 원본 안전 소스 / TTL / 공식 CM / 가제보 모델 미수정.
- Cycle30 raw trace 2.6M 개 이벤트로 overload, Cycle31 symbol-name identity 실패를 재현하지 않기 위해: 메타데이터 3종 전체 + callback_start/end는 `$ctx.procname`으로 CM에 한정해서만 기록한다. 필터/clock anchor preflight 실패면 **NO GOAL**. 기존 C37 한 개 CI simulation Goal 원본 실행기만 재사용하고 결과는 **진단용**, 절대 release/Owner acceptance로 승격하지 않는다.

## RED→GREEN→REFACTOR→REVIEW→COMMIT
1. RED: 기존 C04 부재한 `first RMW source pair + mapped cmd_vel callback range` classifier 신규 3개 순수 테스트 실패, 잘못된 source→monotonic epoch 직접 차감 FAIL-CLOSED 검증.
2. GREEN: public `d06/live/g07_cycle05_cm_callback_window.py` 정확한 CM handle 확인(기존 C31), ROS callback 시작/끝 짝짓기 및 anchor clock-domain 검증; RMW source gap은 같은 SYSTEM 내 source-source duration만 비교. Observer mono window로 trace-time correlation. 원인 입증 플래그 항상 false.
3. REVIEW: provenance/clock step/duplicate proc/CM input callback pair missing/trace event limit에서 진단 HOLD. 새로운 ROS Goal command publisher 추가 없음.
4. 공개 L0 실제 RED→GREEN + 같은 CI 런타임에서 LTTng procname filter 사전검증. Tracepoint 과다 수집/필터 미지원이면 **이 단계에서 중지**.
5. 실제 공개 Harmonic+Nav2 CI **진단용 단일 Goal 1회만**: 기존 C37 original private SHA `966886c4627deb2bb3b37111fe336eeee6b9ebb4`, official Waffle/Nav2/14-topic/native STOP/Guard shutdown 유지. First source gap 하나의 callback duration 및 overlap만 sanitized numeric 출력. Trace가 safety timing에 영향을 줄 수 있으므로 이 Run은 120ms release GREEN 증거가 아님.
6. 결과가 callback 내부 장시간 실행 후보이면 공식 Nav2 `base_shift_correction`과 scan staleness/stop zone geometry의 **최소** A/B 계획만 조건부 제시. Callback 자체가 짧으면 TF tuning 하지 말고 Executor/DDS ready queue 쪽을 좁힌다. root cause 불명확하면 다음 Moving Goal 반복 금지.
7. 교육용 보고서: RED/GREEN 실제 테스트 로그, 최초 시계 교차 오류, 실제 callback overlap, 후보/반증, 미검증, exact branch/SHA/Run ID, 편집 파일과 실행 명령, user WSL2 NOT_RUN, main NOT_MERGED 기록. 단발 release CI workflow 철회.

## 별도 인수 경계
- 이번 tracer 진단 L2가 Success인 것만으로 `CM_120MS_RELEASE=PASS` 불가. **Tracer OFF** 원래 안정화 실행기로 120ms CM RMW/Observer + Guard/CM150ms/ScanOdomClock300ms 같은 실제 Goal에서 한 번에 통과하는 별도의 공개 L2 이후에만 Owner WSL2 한 번을 허가.
- 원래 SW 정지는 실제 인증 E-Stop 아님. `AXIA_MVP_DEMO_ACCEPTED=HOLD`; `OWNER_WSL2_MOVING_L3=NOT_RUN`.
