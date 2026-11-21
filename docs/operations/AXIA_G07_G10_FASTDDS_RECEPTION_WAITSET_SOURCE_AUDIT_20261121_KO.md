# AXIA G07 G10 — Fast DDS Jazzy RMW 첫 수신/Executor wait-set 소스 경계 감사

## 검증 대상/상태

- 상태: **SOURCE_CODE_BOUNDARY_CONFIRMED / FIRST_CAUSAL_ROOT_UNPROVEN / CI_L2_HOLD**.
- 본 자료는 ROS 2 / Gazebo 신규 실행 결과가 아니다. 기존 native #44870974857과 #44870371777의 숫자 증거를 공식 Jazzy RMW 구현과 연결한 **읽기 전용 분석**이다.
- 원본 MultiThreadedExecutor 2 workers, CM120/Guard150/Scan·Odom·Clock300, 실제 Goal/Cancel, 정답·TODO 저장소 경계, safety STOP과 인증된 E-Stop의 구분을 유지한다.

## 공식 Jazzy RMW 구현 확인

[ros2/rmw_fastrtps `jazzy` rmw_take.cpp](https://github.com/ros2/rmw_fastrtps/blob/jazzy/rmw_fastrtps_shared_cpp/src/rmw_take.cpp#L44-L65)는 `_assign_message_info`에서 `rmw_message_info_t.source_timestamp = DDS SampleInfo.source_timestamp`, `received_timestamp = DDS SampleInfo.reception_timestamp`, `publication_sequence_number = sample_identity.sequence_number`을 각각 직접 복사한다. **rclpy callback의 host monotonic timestamp와 동일한 시계가 아니다.** Jazzy `rmw_take_with_info`는 `_take`를 통해 실제 DDS DataReader `take()` 결과의 `SampleInfo`를 반환한다.

[ros2/rmw_fastrtps `jazzy` rmw_wait.cpp](https://github.com/ros2/rmw_fastrtps/blob/jazzy/rmw_fastrtps_shared_cpp/src/rmw_wait.cpp#L146-L241)는 DDS DataReader StatusCondition을 wait-set에 등록하고 `fastdds_wait_set->wait` 후 `get_first_untaken_info`로 준비 여부를 판정한다. Python `_wait_for_ready_callbacks` 스택과 idle worker만으로 **RMW ready 이전**인지 **DDs Reader 수신**인지 **OS native middleware thread 스케줄링**인지 확정할 수 없다.

## 실증된 첫 구간 대조 (상대 간격만)

| 실제 실행 | First callback gap | 동일 발행자 Source | original DDS Received | 독립 수신 |
|---|---:|---:|---:|---:|
| #44870371777/C1, CM seq+1 | 388.878ms | 50.019ms | 382.004ms | 독립 Receiver ~50ms |
| #44870974857/C1, CM seq+1 | 361.513ms | 50.457ms | 354.987ms | 독립 Receiver 50.412ms |
| #44870974857/C2, Scan Seq+1 preGoal | 600.503ms | 107.857ms | 599.696ms | 정확한 Header bag 107.738ms |

**보수적 판정:** 원래 Observer 프로세스 내에서 DDS reader 수신부터 rclpy callback까지의 경로에 정상 독립 Receiver와 다른 긴 간격이 존재한다. `Source`가 정상이라서 Gazebo/CM 발행 중단을 최초 원인이라고 볼 증거는 없다. 독립 bag의 동일 Header는 independent publication sequence identity를 증명하지 않는다. `DDS reception timestamp`가 reader에 늦게 기록됐다는 수치는 있지만, native Fast DDS listener 자체가 중지된 것인지, OS thread schedule/futex/transport인지 인과 증거가 없으므로 `ROOT_UNDETERMINED`.

## 실험 중복·금지 목록

- #211 S1 writer lock/json/flush 수 밀리초 이하 — 원인 근거 없음, Observer `_write` 재설계 금지.
- #213/#214 EventsExecutor native/L1 `SystemError` → **REJECTED**.
- #44870974857 20ms bounded `MultiThreadedExecutor.spin_once` **0/2 FAIL** → REJECTED. 실제 `_wait_for_ready_callbacks` 내부에서 여전히 지연.
- G07 `p2_g07_owner_env_parity.py`는 Owner와 CI 모두 `RMW_IMPLEMENTATION`이 미지정 또는 `rmw_fastrtps_cpp`만 허용하며 25개 패키지·5개 공식 파일 고정 SHA를 검사한다. 이미 D08 #208에서 검증된 Cyclone DDS는 **D08 범위의 증거**이며 G07 Owner lock을 변경/우회하지 않고는 G07 release 후보로 승격 불가. 별도 D08 A/B 복제 금지.
- Public native workflow `FASTDDS_BUILTIN_TRANSPORTS: UDPv4`와 `FASTRTPS_DEFAULT_PROFILES_FILE` override 금지 검사 존재. 이는 **환경 설정 확인**이고 실제 DDS transport packet trace까지 검증했다는 뜻은 아니다. SHM #6535 유사 333ms가 근본 원인이라는 주장은 금지.

## G10 다음 최소 확인 (Goal 전 gate 포함)

- 공개 native job의 정확한 RMW 구현을 `rclpy.get_rmw_implementation_identifier()`로 **실제 실행 전** 확인하고 결과를 기록. 현재 parity 보고서의 `rmw_effective_class=rmw_fastrtps_cpp`는 코드상 고정 문자열이므로 **실제 확인이라고 간주하지 않는다.**
- 최초 Gap에서 원래 process/independent Receiver *동일 publisher pair*의 Source/Received/Seq를 재사용하고, RMW 상태 메시지와 안전 TTL을 두 시간축 내부 간격으로만 연결한다. 새 `rcl_wait` C++ tracer/패키지 추가는 증거상 꼭 필요한 경우가 아니면 MVP 범위 밖.
- Safe Guard, CM, Supervisor 내부 전달 age는 독립적으로 검증. 외부 Observer가 늦더라도 안전 노드의 120/150ms 위반이 없다고 자동 결론 내리지 않는다.
- 인과 입증된 경계에 최소 수정 + 실제 red/green + 새 exact SHA의 real Gazebo Moving 2/2 전에는 WSL2 Owner command 출고 금지.

**현재:** G10=HOLD, G20 read-only alignment underway, G30=HOLD, OWNER_L3=NOT_RUN, MAIN=NOT_MERGED, CERTIFIED_ESTOP=false.
