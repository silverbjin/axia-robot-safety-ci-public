# 공개 CI의 검증 수준과 금지된 인수 승격

| 단계 | 검증 가능한 대상 | 절대 증명하지 못하는 것 |
|---|---|---|
| Canary | 표준 GitHub-hosted Runner의 실제 쉘 실행 | ROS/Gazebo |
| Unit | 독립 Python Scan 수신 벽시계 간격, SHA256 비교 | 실제 scan callback monotonic 지연, S01 FSM |
| Jazzy DDS | 실제 ROS 2 middleware의 합성 pub/sub | Nav2/AXIA Supervisor, Goal 소유권 |
| Gazebo 3×/10× | 공식 Waffle/Nav2 무주행 토픽·종료 관찰 | 보호정지/Goal Cancel/odom 정지 인수 |
| Instructor Private | 강사용 S01-S05 및 G00/G03/G04 통합 | 인증 산업용 E-Stop |

실제 강사용 시험은 원래 Private 저장소와 별도 Cloud Runner에서 완료해야 하며 사용자 로컬 WSL2는 최종 인수 전용이다.

기존 `scan_timeout_sec=0.5` 제안 값을 합리화 없이 완화하지 않는다. Receiver wall-time, Supervisor callback monotonic, Gazebo RTF는 서로 다른 계측이다. `gate_accepted=false`, `certified_estop_verified=false` 유지. `main` 병합은 승인 전 금지.
