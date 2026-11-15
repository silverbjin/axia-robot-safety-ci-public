# C-06 공개 CI 검증 범위 (C-02~C-06 전체의 실제 성능 검증과 구별)

- 공개 Student SHA: `dff7b4a2710525a72287f5416b7b613a9d979f1e`. CI는 공개 학생 저장소만 checkout합니다.
- 공개 인수 게이트: Fixture 무결성, 학생 파일 배포/해시, 코드 누출 방지, TODO EXPECTED_RED, 실행기 문법·런타임, 교육 ROS transport의 기존 L1 증거.
- 비공개 Instructor C-02~C-04 정답 모델 코드와 Hidden Test는 공개 CI에서 실행하지 않습니다. Python 3.13 로컬 테스트를 별도 대장에 구분합니다.
- C-05 실제 ROS 2 Jazzy L1: [Run 43720178979](https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/43720178979), 8개 DiagnosticArray, 100ms 목표/99.814~100.201ms 측정, cmd_vel 발행자 0. ROS는 교육용 별도 토픽이고 생산 Guard TTL은 미검증입니다.
- C-06 공개 CI PASS만으로 Instructor ML→ROS 전체 통합, Owner WSL2, Gazebo, certified E-Stop, 강의 12h 리허설을 승인하지 않습니다.
- Release: `RELEASE_APPROVED=false`, `OWNER_WSL2_VERIFIED=false`, `MAIN_MERGED=false`; 사용자의 일괄 현장 인수와 main 병합 승인은 별도입니다.
