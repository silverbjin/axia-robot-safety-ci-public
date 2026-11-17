# AXIA G07 Cycle04 — 공식 CM cmd_vel 콜백 식별 (실제 NO_GOAL L1)

## 근거와 범위
- Cycle02 NO_GOAL TF/odom/clock 각 최대 334~340ms. Cycle03 NO_GOAL Run #43992804389에서 세 최대 수신 공백 교집합 **333.601ms**, 실제 Moving Goal 원인 규명은 여전히 불가.
- Moving 실제 두 Run #43898345608/#43981875149에서 CM RMW source max 128.644/133.659ms > 120ms. 원래 Guard 150ms hard TTL 위반은 현장 별도 158.008ms 사례. **HOLD**.
- 기존 Cycle30 추적은 전체 2,611,716 이벤트에서 CM callback 849개를 확보했지만 cmd_vel 콜백 핸들을 symbol name으로 식별하지 못했다.
- 이미 구현된 공개 `d06/live/g07_cycle31_cm_topic_callback_identity.py`는 `rcl_subscription_init→rclcpp_subscription_init→rclcpp_subscription_callback_added` 핸들 연결 알고리즘; L0 7/7 green. **핵심 미검증은 실제 활성화된 공식 CM 노드의 원본 메타데이터**.
- 이번 Cycle04는 콜백 실행시간이나 TF 대기를 계측하지 않고, ***구독 메타데이터 3종만*** LTTng로 읽는 실제 Jazzy+Gazebo/Nav2 NO_GOAL 실험. 이벤트 raw/PID/pointers는 공개하지 않는다.

## 체계적 RED→GREEN→REFACTOR→REVIEW→COMMIT
1. RED: 기존 Cycle31의 순수 resolver를 기준선으로 재사용하되, 실제 PID·procname/토픽 후보가 다중일 때 fail-closed로 거부하는 새 진단 집계 계약 3건. 신규 평가 어댑터 파일이 없음을 먼저 확인.
2. GREEN: 공개 진단만 추가 (`d06/live/g07_cycle04_cm_metadata_audit.py`), 기존 `resolve_cm_cmdvel_handles` 호출, 등록된 프로세스 이름 `collision_monitor` 혹은 Linux 15문자 잘림 `collision_monit`만 허용, 해당 CM PID 하나/토픽 핸들 하나 이상, 모든 필수 tracepoint 수신 시에만 `CM_INPUT_CALLBACK_HANDLE_IDENTIFIED_NO_GOAL`; 실제 C++ 콜백 시간이 입증된 것은 아님.
3. PUBLIC L0: RED3→GREEN3 + 기존 Cycle31 suite, ROS/Gazebo 없는 정확한 데이터 기반 테스트.
4. PUBLIC L1: 이전 성공한 official Nav2 NO_GOAL sealed startup `scripts/p2_no_goal_smoke_ci.sh` 재사용. **활성 CM node 생성 전 LTTng 켜고 subscription metadata event 3종만 기록**, 기존 14-topic Recorder/CM/Localization/Nav2 Shutdown 검증. callback_start/end 포함하지 않아 기존 260만 이벤트 재수집 금지.
5. REVIEW: 토픽 핸들 연결 성공 여부/실제 tracepoint count/process metadata만 기록; 실패 시 최초 missing chain/timestamp/tracepoint를 보고 HOLD. 내부 콜백 처리지연 원인은 이 데이터만으로 입증 불가.
6. 완료 시 교육용 보고서에 원본 증거·실행 명령·Run ID/정확한 source SHA/검증 제한·학습 질문/다음 최소 후보 명시, 보고서 commit. 임시 release workflow는 성공/실패 결과 판정 뒤 철회. **Moving Goal은 아직 금지**, 원인 분리 L1이 통과해야만 Cycle05에 진입.

## 금지 사항
- 원래 Safety CM/Guard/Supervisor/Nav2 수정, `base_shift_correction` 값 변경, 새 속도 publisher/Goal, 120/150/300ms 완화, 무제한 LTTng callback trace, SW Stop을 certified E-Stop으로 홍보, Owner WSL2 재시도, main 자동 병합.

현재 `CM_120MS_RELEASE=HOLD`, `AXIA_MVP_DEMO_ACCEPTED=HOLD`.
