# AXIA D11-LIVE-REPLAY-01 — AE vs IF 오프라인 사건 수사실

**학습 목표 1:** AutoEncoder 기반 정상상태 재구성 원리 이해.  
**학습 목표 2:** 재구성 오차 기반 이상상태 판정 실습.

D10의 기존 오프라인 Replay **원본·Window·품질 검증기**를 두 번 재사용하고 IF/AE 기록 점수를 같은 Window에서 결합하는 단일 HTML 강사용 데모입니다. 180분 본 수업 중 기존 시연·토론 시간에 **12분**을 편입합니다. **새로운 모델 훈련/추론, ROS 2/Gazebo/Nav2·cmd_vel·SW Stop·인증된 E-Stop 제어는 없습니다.**

데이터: SYNTHETIC_COURSE_FIXTURE(seed2409, 합성10Hz), 전체 Raw 4,599/46 Trace, Test 100 VALID(정상82/이상18)+4 품질 상태행. 화면의 IF와 AE 원점수는 **서로 다른 척도**이므로 별도 그래프·별도 cutoff로 보여 줍니다. 실제 TurtleBot3 계측이 아닙니다.

## 코드·보안 경계

| 저장소 파일 | 설명 | 공개 여부 |
|---|---|---|
| d10/replay/build_replay.py | 기존 원본/score 계약 검증기. **수정하지 않음** | 공개 |
| d11/replay/build_replay.py | IF/AE CSV 각각 위 검증 후 동일 Trace/Window/시간·정답으로 조인 | 공개 |
| d11/replay/replay_template.html | 자체 포함 CSS/Canvas/JS, 정답 숨김/공개 | 공개 |
| d11/replay/test_replay.py 및 test_browser.py | 독립 가짜 점수 기반 L0·브라우저 테스트 | 공개 |
| d11/replay/owner_one_shot.sh | 강사의 **비공개 로컬 자료만 읽는** WSL2 실행기 | 공개 |
| 강사 private day10/day11/reference_outputs | 기존 IF/AE 실제 기록 점수·메타데이터 및 생성 HTML | **비공개** |
| 학생 공개 block_C/day11 | 초심자 가이드·수학 TOY·미구현 TODO | **모델 정답 없음** |

공개 CI에는 강사용 score CSV/가중치/비공개 HTML을 올리지 않습니다. 빌더는 두 점수 CSV에 대해 D10 엄격 검증기를 각각 적용하고, 동등한 window_id, timestamp_ns, truth_label, status, 품질 사유만 조인합니다. 누락, 충돌, 잘못된 prediction, 품질 실패의 거짓 NORMAL을 거부합니다.

## 강사 WSL2 원샷과 예상 결과

클론부터 시연까지는 **강사 비공개** D11_LIVE_REPLAY_INSTRUCTOR_GUIDE_KO.md를 이용하십시오. 공개 스크립트는 정확한 40자리 CI GREEN PIN에서 다운로드합니다. 별도 비공개 repo가 없으면 기존 GitHub 인증을 이용해 clone하고, 있으면 지우거나 초기화하지 않습니다.

- 기본 강사 클론: ~/axia_d11_course/axia-robot-safety-instructor/training/block_C
- 기본 HTML: ~/axia_d11_course/AXIA_D11_LIVE_REPLAY_INSTRUCTOR.html
- 최소 진단 압축: ~/axia_d11_course/d11_replay_evidence/d11_minimal_evidence.tar.gz
- 커스텀 경로: AXIA_D11_INSTRUCTOR_BLOCK_C, AXIA_D11_REPLAY_OUT 환경 변수.
- Windows Edge/Chrome에서 HTML을 더블클릭할 수 있습니다. WSL2 explorer.exe 자동 실행 성공은 별도 검증입니다.

예상 패턴(Owner WSL2 미실측):

~~~text
D11_REPLAY_L0_PASS ... traces=14 windows=104 valid=100 quality=4 if_tp=1 if_fp=2 if_fn=17 if_tn=80 ae_tp=18 ae_fp=4 ae_fn=0 ae_tn=78 ros_actual=false gazebo_actual=false model_inference=false
D11_REPLAY_OWNER_HTML_BUILT_AND_REFERENCE_VALIDATED
D11_REPLAY_OWNER_BROWSER_NOT_VERIFIED
D11_REPLAY_OWNER_GENERATED=/home/.../AXIA_D11_LIVE_REPLAY_INSTRUCTOR.html
~~~

## 12분 몰입형 수업 큐시트

| 분 | 조작 | 학생 질문 | 확인할 의미 |
|---:|---|---|---|
| 0–2 | TST_A_00 선택, 모든 답 숨기고 재생 | 전류 급증 중 어느 Window가 의심스러운가? | 증거 먼저 |
| 2–4 | W4 이동, IF/AE 순차 공개 | 두 모델이 같은 결론을 내는가? | 서로 다른 점수·cutoff |
| 4–5 | W5 이동(자동 재숨김) | 다음 Window에서 판단이 바뀌는가? | 시간 순서·미탐 |
| 5–7 | TST_N_02 W4 | 정상 라벨에도 경고가 나올 수 있나? | 오탐(FP) |
| 7–9 | TST_A_04 W8 | 주입 종료 뒤에는 무조건 정상인가? | Window별 판정 |
| 9–10 | TST_Q_01 | 점수가 없으면 0점 NORMAL인가? | INSUFFICIENT_DATA |
| 10–12 | 정답/혼동행렬 공개 | 모델 성능이 곧 인증 안전 기능인가? | TP/FP/FN/TN와 한계 |

정답과 기존 참조 점수는 강사 비공개 가이드에서 확인합니다. 이전/다음 Window로 이동하면 공개 상태와 학생의 예측 선택이 초기화됩니다. 각 모델의 그래프 눈금은 별도이므로 AE MSE가 IF 위험점수보다 큰 숫자로 나와도 모델 비교의 근거가 아닙니다.

## 기대 교육 효과 및 수업 중 측정할 방법

아래는 **교수설계상의 기대 효과이며, 학습효과 실측이나 몰입도 개선율을 주장하지 않습니다.**

| 기대 효과 | 작동 원리 | 수업에서 관찰할 증거 |
|---|---|---|
| 학생 몰입 | 정답 숨김 → 예측 → IF 공개 → AE 공개 → 합성 정답 공개 | 학생이 W4/W5 선택과 이유를 말하는지 |
| AE 정상 재구성 이해 | 같은 Window에서 복원 MSE와 원본 신호를 연결 | 6→8→3→8→6과 x/xhat 차이를 설명하는지 |
| 정량적 이상판정 이해 | 두 개의 독립 경고선과 점수 공개 | MSE 0.01/1.0 TOY 손계산·cutoff 부등호 판정 |
| 품질 우선 습관 | 결측/시각 오류에서 점수 없음 | 불량 상태를 NORMAL=0으로 치환하지 않는지 |
| 오탐·미탐 인식 | 동일 Test에서 IF와 AE 판단 차이를 기록 | FP/FN 및 confusion 계산·의미 설명 |
| 검증 책임 | 합성 기록/과거 reference/현장 실측 구분 | 모델 재학습이나 안전정지를 수행했다고 주장하지 않는지 |
| 운영 안정성 | HTML 단일 파일 오프라인 구동 | 네트워크 없이 Windows Edge에서 14 Trace, 버튼 동작 확인 |

수업 후 학생 d11_report.md에 “예측→공개 후 바뀐 판단 1개”와 “판정 근거 1개”를 추가하도록 질문할 수 있습니다. 정량적인 교육 효과를 주장하려면 실제 학생의 전·후 테스트가 별도로 필요합니다.

## 검증과 실패 복구 경계

**공개 L0:** 독립 가상 점수(IF/AE), C01 원본, 104 Row, Test100+품질4, 조인/시간/예측/품질 fail-closed, Node JS syntax.  
**공개 브라우저 L1:** Linux Chromium/Chrome에 생성 HTML 바이트를 주입해 1920×1080 화면, Window 이동, 숨김/공개, 품질4, Play/Pause, 모바일 레이아웃 확인합니다. **Windows file:// 직접 열기 시험과 다릅니다.**  
**비공개 Owner:** 기존 C03 IF / C04 AE 점수, 참조 메트릭과 cutoff 및 SHA 계약 검사 후 HTML 제작. Model inference는 수행하지 않습니다.

실패 시 CLI의 최초 D11_REPLAY_CONTRACT_FAIL 단계(원본/두 점수/조인/품질)을 확인합니다. HTML 생성 실패는 브라우저 재시도로 고치지 않고, HTML 생성 성공과 브라우저 실행 실패를 구분합니다. 모델을 재학습하거나 임계값을 Test에 맞춰 변경하지 않습니다.

**주의:** 주입 시작부터 Window 종료까지의 간격은 **합성 기록상의 시간 차이**이며 ROS 메시지 지연·SW Stop·인증 E-Stop 타이밍 측정이 아닙니다. 이 항목들은 이번 데모에서 미검증입니다.
