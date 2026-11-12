# AXIA D04 강사 시연 보충 — 단일 이미지의 bbox·class·confidence 눈으로 확인하기

> **범위:** 공식 Python Ultralytics CPU 추론 1장 + 교육용 결과 시각화.  
> ROS 2 Jazzy / Gazebo Harmonic / Nav2 / SW Stop / 인증 E-Stop은 **이 실행에서 NOT_RUN**.  
> 기존 실제 Gazebo·C++ yolo_ros 실시간 D04 시연은 변경하지 않는다.

## 1. 왜 단일 이미지를 다시 추가하는가?

Gazebo 카메라 영상에서 움직이는 Bounding Box만 보여주면 학생은 값의 의미를 이해하기 어려울 수 있다. 공식 샘플 `bus.jpg` 한 장에서 나온 **실제 YOLO 결과를 정지 화면으로 고정**하여 다음의 필드를 1:1 대응시킨다.

- **class:** 검출한 객체 범주. 여기서는 학생·강사 공통 코드를 따라 `person`만 추출한다. 다른 클래스는 모델에 있더라도 이 보고서에서는 필터링한다.
- **confidence:** 모델의 검출 신뢰도(0~1). 확률로 오해하거나 안전 인증, 로봇 거리로 해석하지 않는다.
- **bbox_xyxy:** 이미지 픽셀 좌표 `(x1,y1,x2,y2)`. 좌상단과 우하단이며 폭은 `x2-x1`, 높이는 `y2-y1`. 3D 물리 거리/로봇 충돌 신호가 아니다.

## 2. 강사 WSL2에서 기존 Gazebo 시연과 독립적으로 실행

강사의 기존 `axia_d04_classroom_wsl2_once.sh`는 `--single-image` 옵션을 갖는다. 이 옵션은 **비공개 P1·`gh auth`·Gazebo를 실행하지 않는다.** 공개 학생 저장소의 정확한 소스 SHA `6012336bef42be7f9d74cc9632baea41db555ae9`를 재사용한다. 공식 Ultralytics `yolo26n.pt`, `bus.jpg` 및 Python 가상환경은 이미 존재하면 그대로 재사용한다.

~~~bash
(
  set -Eeuo pipefail

  SHA="D04_NEW_PUBLIC_ENTRY_SHA_TO_BE_PINNED"
  SCRIPT="$(mktemp)"
  trap 'rm -f -- "$SCRIPT"' EXIT

  curl -fsSL --retry 3 \
    "https://raw.githubusercontent.com/silverbjin/axia-robot-safety-ci-public/$SHA/scripts/axia_d04_classroom_wsl2_once.sh" \
    -o "$SCRIPT"

  bash -n "$SCRIPT"
  bash "$SCRIPT" --single-image
)
~~~

**기존 Gazebo 실습을 끝내고 같은 강사 명령에서 단일 이미지를 연속 수행하려면** 위 블록의 마지막 줄만 `AXIA_D04_SINGLE_IMAGE_AFTER_GAZEBO=1 bash "$SCRIPT" --run`으로 변경한다. 기존 `bash "$SCRIPT" --run`은 여전히 Gazebo 전용으로 작동하고, 과거 성공 증거를 보존한다. 수업 운영은 **Gazebo 1회 + 단일 이미지 1회**를 권장한다.

첫 실행은 공개 PyTorch CPU 가중치, Ultralytics `8.4.211` 및 공식 모델·사진을 준비할 수 있다. 모델 다운로드에 실패했다면 코드 결과를 추측해서 성공으로 보고하지 않는다. 학생 캐시 기본 경로를 공유하여 반복 다운로드를 방지한다.

## 3. 실제 결과를 보는 법

실행 후 (실제 값은 모델·이미지에서 직접 출력):

~~~text
D04_SINGLE_IMAGE_BBOX index=1 class=person confidence=<실측> bbox_xyxy=(x1,y1,x2,y2) bbox_wh=(w,h)
D04_SINGLE_IMAGE_BBOX index=2 class=person confidence=<실측> bbox_xyxy=(x1,y1,x2,y2) bbox_wh=(w,h)
...
D04_SINGLE_IMAGE_IMAGE_PATH=/home/.../bbox_class_confidence.png
D04_SINGLE_IMAGE_HTML_REPORT=/home/.../bbox_class_confidence.html
D04_SINGLE_IMAGE_REPORT_PASS persons=<실제 숫자> NO_GAZEBO NO_ROS NO_GOAL NO_SAFETY
~~~

결과 루트는 `~/axia_d04_instructor_single_image_results/teacher_same_code_...`이며 **실행마다 새 폴더를 생성**합니다.

GUI 화면을 확인할 때는 강사 WSL2에서 다음 명령으로 **해당 결과 폴더를 한 번만** 엽니다.

~~~bash
(
  set -Eeuo pipefail
  OUT="$(find "$HOME/axia_d04_instructor_single_image_results" -mindepth 1 \
    -maxdepth 1 -type d -name 'teacher_same_code_*' -printf '%T@ %p\n' |
    sort -nr | head -n 1 | cut -d' ' -f2-)"
  test -f "$OUT/bbox_class_confidence.png"
  test -f "$OUT/bbox_class_confidence.html"
  echo "D04_SINGLE_IMAGE_RESULTS=$OUT"
  explorer.exe "$(wslpath -w "$OUT")"
)
~~~

Windows 파일 탐색기에서 `bbox_class_confidence.html`을 더블클릭합니다. 브라우저에 **BBox가 그려진 실제 이미지와 각 class/confidence/bbox 표**가 함께 나타납니다. `bbox_class_confidence.png`만 열어도 라벨을 확인할 수 있습니다. 기존 Gazebo 창을 무한 반복 생성했던 문제를 피하기 위해 **실행기가 `xdg-open` 또는 이미지 뷰어를 자동으로 시작하지 않습니다.**

## 4. 강의실 시연 질문 순서

1. "실제 이미지에서 **사람 Bounding Box가 몇 개** 있습니까?" → 그림의 박스 번호와 터미널 `index`를 비교합니다.
2. "`class=person`은 무엇을 뜻합니까?" → 사람 범주이지 사람의 신원이나 추적 ID가 아닙니다.
3. "`confidence=0.9xxx`는 어떤 뜻입니까?" → 검출 모델이 부여한 신뢰도이며 **안전 확률/인증이 아닙니다.**
4. "`bbox_xyxy=(...)`에서 로봇과의 거리를 알 수 있습니까?" → **아니요.** 사진의 2D 픽셀 경계일 뿐 거리센서 값이 아닙니다.
5. "이것을 학생의 `select_person()`에 연결할 수 있습니까?" → 공통 필드 의미를 설명할 수 있지만, 이번 실습의 **실제 추론 CSV**와 기존 학생 **4×4 합성 CSV**는 서로 다른 데이터 세트입니다.

## 5. 실제 코드의 위치 및 검증 범위

| 역할 | 공개 파일 |
|---|---|
| 실제 Python CPU YOLO 추론·person 필터 | 학생 저장소 `block_B/day04/yolo_single_image_demo.py` (SHA 고정) |
| 모델·사진 준비·CSV/manifest 작성 | 학생 저장소 `block_B/day04/run_teacher_yolo_demo_once.sh` (SHA 고정) |
| bbox/class/confidence 주석 PNG·HTML | 공개 CI 저장소 `scripts/d04_instructor_single_image_report.py` |
| 강사 독립 원샷 | 공개 CI 저장소 `scripts/axia_d04_instructor_single_image_once.sh` |
| 기존 Gazebo + YOLO·관리형 종료 | `scripts/axia_d04_classroom_wsl2_once.sh --run` |

**성공 기준:** 실제 모델 추론의 `detections.csv`가 생성되고, SHA256 manifest 일치, `person_count > 0`, 좌표가 이미지 범위 내임을 확인하며, 같은 숫자를 주석 이미지·HTML에 출력한다. `D04_SINGLE_IMAGE_REPORT_PASS`가 없으면 시연 성공으로 보고하지 않는다.

**검증 분리:** 공개 CI에서 실행한 실제 CPU 추론/주석 생성에 한해 결과를 PASS로 표시한다. 가상 CI에서 Python 보고서만 테스트한 결과는 실제 모델 성공으로 승격하지 않는다. 사용자 WSL2에서 브라우저로 결과를 연 화면은 사용자의 현장 확인이다. 강사 비공개 Actions는 사용하지 않는다.

**라이선스:** Ultralytics 공식 모델 및 `bus.jpg`는 강사 PC로 직접 내려받고 공개 저장소·CI Artifact에 원본 가중치나 사진을 업로드하지 않는다. AGPL-3.0/Enterprise 이용 조건을 확인한다. 수업 시연의 로컬 CPU 모델과 Gazebo·C++ ONNX 모델은 별개다.
