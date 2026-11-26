# AXIA DAY 02 — 듀얼 G07 워크북 v4 전체 PPTX 제작·main 문서 인수 QA

**2026-11-26.** `WORKBOOK_PPTX_LOCAL_RENDER_QA_PASS`; `STUDENT_MAIN_DOCS_CI_GATE_PENDING`; `NEW_GAZEBO_L2_NOT_RUN`; `INSTRUCTOR_PRIVATE_ANSWER_STAYS_PRIVATE`.

## 실제 제작·교차 QA
- **PPTX 40장**, **PDF 40페이지**, **발표자 노트 40/40장**, **렌더 40/40장**, slide boundary overflow 0건.
- A/B Master-first: 기본 U00~U13 14×2=28장, 심화 A01~A06 6×2=12장, **완성형 프롬프트 20개/프롬프트 이유/실행 명령/예상 결과/AI 응답 3개 QA**.
- 정확한 PPTX 파일 SHA256: `3dba11b1f18cde17c3cd8d63caea7f8dc79b1a91598d9d09992d42a15af709bf`.
- 정확한 PDF 파일 SHA256: `ee6ca81ff804be3ca26f03d10159598d3a660a6bf57ff5e77d6da0accc2cd731`.
- PDF 텍스트 추출 40/40, 슬라이드별 Unit ID 40/40, 모든 Unit 20개의 Prompt 마지막 문장 포함 확인.
- 해당 **PPTX/PDF 바이너리 파일은 ChatGPT 산출물 링크로 배포**했지만 현재 GitHub main 커밋에는 바이너리를 업로드하지 않았습니다. README와 Manifest가 이 사실을 명시합니다. 이 문서를 GitHub binary PASS의 증거로 사용하지 마십시오.

## 실제 검증된 ROS/Gazebo 소스 인수 (오늘 재실행 안 함)
| | 성공 | 실패 |
|---|---|---|
| Student runtime | `f7edb2d126502eeeed58ae014adadc7a2096d41b` | `a04f9a7da8d54bbd9f944d05388792cb706adf28` |
| Public CI source | `64ba0161e66126b4743b4b12a859f4a5349ae58a` | `8e03ac0a912ca9b81bdddda70212e52e6d804389` |
| Native Moving | #44965035965 **2/2 PASS** | #44914827138 **0/2 FAIL** |
| Owner L3 | 11/22 RAW numeric/lifecycle `PASS_SCOPED` | NOT_RUN |

Original machine `HOLD_RAW_REVIEW_AND_VISUAL_PENDING` unchanged, FastDDS/RMW root `UNDETERMINED`, certified E-Stop false. Safety TTL(120/150/300ms) unchanged.

## 이번 main 통합 범위
1. Student main: `special_lecture/day02_workbook_v4/` 교육용 README·20-Unit map·Manifest·L0 verifier **4개 텍스트 파일만 선택적 병합**, 기존 `block_B/C/D` 운영 런타임 전부 보존.
2. Instructor private main: `docs/training/day02/` 독립 강사용 해설/채점/시나리오 자료. **강사 정답 공개 금지**.
3. Public CI main: 본 보고서 + `.github/workflows/axia-day02-workbook-v4-main-l0.yml`. 검증기는 학생 통합 후보 정확 SHA에 고정하고 반례 RED→GREEN, 학생 공개 자료 노출 검사, 검증 수준 레이블만 확인.

## 독립 L0 CI 게이트
- Workflow는 기존 Native Gazebo 인수의 재실행이 아닌 문서 프로비넌스 검증, 학생 릴리스 SHA·unit count·기존 G07 운영 코드 무변경·안전 검증 레벨을 확인합니다.
- 실제 새 WSL2, Gazebo Moving, 사용자 화면 검수는 NOT_RUN입니다.
- 기존 학생/CI 여러 Draft PR의 오래된 Base라인을 main으로 통째로 병합하지 않습니다. 사용자 명시 승인으로 이번 문서 변경만 merge합니다.

## 남은 범위
- 원본 PPTX/PDF의 GitHub binary 업로드는 이 텍스트 GitHub 도구로 수행하지 않았으므로 후속 별도 자산 업로드 필요. **사용자에게는 이미 40장 전체 PPTX/PDF를 대화 아티팩트로 제공**했습니다.
