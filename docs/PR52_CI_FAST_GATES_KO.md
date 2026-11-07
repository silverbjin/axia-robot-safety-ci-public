# PR52 CI 경량 게이트 운영 정책 (2026-11-07)

## 실행 원칙
- L0: 매 브랜치 Push에서 pr52-fast-policy.yml을 실행한다. Python 단위 테스트와 문법 검사만 수행하며 비공개 체크아웃, ROS 설치, Gazebo는 사용하지 않는다.
- L1: 독립 ROS / Fake ROS 사전 검증은 아직 구축되지 않았다. L0 통과를 L1 통과로 보고하지 않는다.
- L2: pr52-cloud-g00-real.yml은 전용 요청 파일 변경 또는 수동 실행 시에만 동작한다. 정확한 비공개 SHA를 고정한다.
- L3: G00~G04 통합 인수와 3회 반복은 별도 증거를 요구한다. 이번 변경으로 PASS가 되지 않는다.
- RED → GREEN → REFACTOR → REVIEW → COMMIT. 안전 관련 테스트 생략은 허용되지 않는다.

## 명시적 G00 3회 실행 요청
feat/secure-instructor-cloud-bridge 브랜치에서 소유자 silverbjin만 다음 명령으로 실제 시뮬레이션을 요청할 수 있다.

    mkdir -p .github/axia
    printf 'REQUEST_G00_3X_SIM_ONLY: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > .github/axia/pr52-g00-3x.request
    git add .github/axia/pr52-g00-3x.request
    git commit -m 'ci: explicitly request protected G00 3x simulation'
    git push origin feat/secure-instructor-cloud-bridge

이 명령은 시뮬레이션 수행 요청이므로 사전 조건을 충족했을 때만 실행한다. 소스나 워크플로 파일만 Push해도 실제 G00를 자동 실행하지 않는다.

수동 workflow_dispatch UI는 GitHub에서 워크플로가 default branch에 등록되어 있어야 표시될 수 있다. main 병합 전에는 위 전용 요청 파일 방식으로 실행한다.

## 유지된 보안 및 검증
- 비공개 SHA: b75d971b3d6655105ad9055bcbbcb043ac2feaa8
- 보호 환경: axia-instructor-sealed
- 저장소, 실행자, 브랜치 조건 유지
- Goal/Fault 직접 우회 금지, 비공개 소스와 원시 rosbag2 업로드 금지, 실행 후 소스 정리
- L0 정적 검사 PASS는 실제 ROS2/Gazebo/Goal/정지/인증 E-Stop 성공이 아니다.

## 남은 장애
이전 G00 실행의 PREFLIGHT_FAKE_ROS_FAILED / ROS_DIAGNOSTIC_UNAVAILABLE는 아직 해결되지 않았다. 공개 오류 분류기 회귀 테스트만 추가했다. 비공개 ROS Fake 테스트의 독립 실행 및 실제 원인 수정이 필요하다. main 병합은 별도 사용자 승인이 필요하다.
