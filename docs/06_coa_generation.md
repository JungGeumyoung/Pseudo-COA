# 06. COA 생성

situation 하나에서 COA(order)를 생성해 시뮬레이터 입력으로 만들기까지의 흐름이다. 코드는 `generation/`에 있다.

```
 data/situations/<id>.json ─┐  situation (익명화 input)
 doctrine/doctrine_pack.json ─┤  교범: 동사 정의 + 명령 구성 요소 + 임무 유형별 조항 (조건 D, DF)
 data/pseudo_gt/*.json ──────┤  pseudo-GT 예시 k건 {input → order}         (조건 F, DF)
                        ▼
              generation/prompt.py   system(명령 규칙) + user
                        ▼
              generation/backends.py  생성 모델 (구조화 출력: schema/order.schema.json)
                        ▼
              tools/validate_order.py   오류 0이어야 통과
                        ▼
              tools/case_io.py sim_view  input + 새 order + scenario  ──▶  pysc2
```

## 실행

```bash
# 프롬프트만 보기 (모델 없이)
python3 generation/generate_coa.py --case kb2_023 --dry-run > prompt.txt

# 50건 중 하나로 생성 → 검사 → 시뮬레이터 입력
python3 generation/generate_coa.py --case kb2_023 --out runs/kb2_023.json --sim-out runs/kb2_023.sim.json

# 새 상황 (input 블록 꼴 JSON. 시뮬레이터 입력은 scenario가 있어야 만들 수 있다)
python3 generation/generate_coa.py --situation my_situation.json --mission-type 지역방어 --out runs/new.json
```

| 옵션 | 기본값 | 뜻 |
|---|---|---|
| `--cond` | `DF` | `Z` situation만 / `D` +교범 / `F` +예시 / `DF` +교범+예시 |
| `--k` | 3 | 예시 수 |
| `--backend` | `claude:claude-sonnet-5-5:medium` | `claude:<model>:<effort>`(Claude Code CLI, 로그인 필요) 또는 `openai:<base_url>\|<model>`(vLLM·Ollama 등 OpenAI 호환 서버, `openai` 패키지 필요) |

결과 JSON은 `{id, mission_type, cond, examples, order, validation: {ok, errors, warnings}, gen}`이다. 종료 코드는 검사 오류가 없으면 0이다.

## 프롬프트 구성 (`generation/prompt.py`)

- **system** (`GEN_SYSTEM`, 약 3천 자): 명령의 형태, 전투편성, 과업 동사 32개와 동사별 필수 params, timing, 전투력 조건, 참조·좌표 규칙. 사례 생성기(데이터 구축용)의 규칙 가운데 order에 해당하는 것만 옮겼다.
- **user**: 아래 순서로 붙인다.
  1. (D) 교범 1: 과업 동사의 교범 정의 32개 조항. 교범 2: 명령의 구성 요소 16개 조항(임무 문장, 의도, 작전개념, 가정, 예비). 교범 3: 그 임무 유형의 조항 8개.
  2. (F) 예시 k건: `[situation]` + `[order]` JSON. 공백 없이 압축해서 넣는다.
  3. 이번 과제: `[situation]` JSON
- **예시 고르기** (`pick_examples`): 같은 임무 유형을 먼저 고른다. 그 안에서는 가용 부대 수 차이 + 0.5 × 적 부대 수 차이가 작은 순으로 고른다. 50건 안의 사례가 대상이면 그 사례와 **같은 전투**는 예시에서 뺀다(leave-one-out). 같은 전투는 제목의 지명이나 고지 번호가 겹치는 경우다. 예: 351고지 전투 kb2_019 ↔ kb2_029.
- 프롬프트 길이(kb2_023, system 포함): Z 1.0만 / D 5.2만 / F 5.7만 / DF 9.8만 자.

## 생성 모델을 바꿀 때

`generation/backends.py`의 `generate(system, user, schema) -> (obj, meta)`를 같은 서명으로 구현하면 된다. 구조화 출력을 지원하지 않는 모델이면 응답에서 첫 JSON 객체를 꺼낸다(`_extract_json`). 출력 order는 약 8KB다. 출력 한도가 작은 모델은 잘릴 수 있다.

## 생성 품질 실험 (`experiment/`)

few-shot으로 쓸 만한 COA가 나오는지 시뮬레이터 없이 먼저 본 실험이다. 50건 모두를 leave-one-out으로 돌렸고, 조건은 Z / D / F / DF 네 가지다.

```bash
python3 experiment/run_gen.py --model claude-sonnet-5-5 --workers 4   # 200건 생성 → results/gen/<cond>/<id>.json
python3 experiment/score.py                                           # 규칙 검사 + GT 구조 일치 → results/scores.jsonl
python3 experiment/judge.py --model claude-opus-5-5 --workers 4       # LLM 블라인드 심사 (GT 포함) → results/judge/
python3 experiment/report.py                                          # → results/REPORT.md
```

평가는 세 층이다.

1. **규칙 검사**: `validate_order` 오류가 0인 비율. 시뮬레이터에 바로 넣을 수 있는가를 본다.
2. **pseudo-GT와의 구조 일치**: 부대별 배치 거리(km), 주력·예비 구성 일치(Jaccard), 예비 투입 조건 일치, 핵심 지형·과업 목표 지형 일치, 임무 동사 일치. GT는 역사적 재구성이지 최적해가 아니다. 그래서 이 값은 "실제 지휘관과 얼마나 비슷하게 판단했나"를 뜻하고 "얼마나 좋은가"를 뜻하지 않는다.
3. **LLM 심사**: 심사 모델은 situation과 order 하나만 보고 다섯 항목(임무 부합, 지형 활용, 적 대응, 전투력 운용, 협조·실행성)을 1~5점으로, 전체를 1~10점으로 매긴다. GT order도 같은 프롬프트로 출처를 숨기고 채점해 기준선으로 쓴다.

최종 판단은 시뮬레이션이다. 같은 scenario에서 생성 COA와 GT COA를 돌려 결과(`history.outcome_metrics` 꼴)를 비교한다.

## 실험 결과

2026-10-19 실행. 생성 모델은 claude-sonnet-5-5(effort medium), 심사 모델은 claude-opus-5-5(effort medium)다. 50건 × 4조건 = 생성 200건, 심사 250건(GT 50건 포함)이다. 비용은 생성 $44, 심사 $35다. 전체 표는 [`experiment/results/REPORT.md`](../experiment/results/REPORT.md)에 있고, 생성된 COA는 `experiment/results/gen/<조건>/<id>.json`에 있다. 교범은 교범 1·2·3(동사 정의, 명령 구성 요소, 임무 유형별 조항)이 들어간 판이다.

| 지표 | Z (규칙만) | D (+교범) | F (+예시) | DF (+교범+예시) | GT |
|---|---|---|---|---|---|
| 검사 통과(오류 0) | 90% | **74%** | 90% | 92% | 100% |
| 심사 overall (1~10) | 5.18 | 5.28 | **5.52** | 5.48 | 5.36 |
| 예비 투입 조건 대상이 GT와 같음 | 15% | 19% | **34%** | 30% | — |
| 과업 동사 집합 일치 (J) | 0.36 | 0.37 | **0.51** | 0.50 | — |
| 과업 목표 지형 일치 (J) | 0.31 | 0.37 | 0.36 | **0.44** | — |
| 부대 배치 거리, GT 대비 (km, 기준선 1.73) | 1.63 | 1.63 | 1.56 | 1.53 | 0 |

같은 사례끼리 짝지은 심사 overall 차이(95% 부트스트랩 구간)는 다음과 같다.

| 비교 | 차이 |
|---|---|
| F − Z | +0.34 [+0.18, +0.50] |
| DF − Z | +0.30 [+0.16, +0.44] |
| D − Z | +0.10 [−0.08, +0.26] |
| DF − F | −0.04 [−0.22, +0.14] |
| F − GT | +0.16 [−0.06, +0.40] |

**읽는 법**

1. **pseudo-GT 예시(few-shot)는 효과가 있다.** 예시를 주면 심사 점수가 0.3점 오르고 GT와 같은 수준이 된다(F가 GT보다 높음 16건, 같음 25건, 낮음 9건). 조건 쓰는 법, 동사 선택, 예비 투입 대상도 GT에 가까워진다.
2. **지금의 교범 묶음은 효과가 거의 없다.** 교범만 주면(D) 검사 통과율이 오히려 떨어진다. 실패 13건 중 11건은 `concept.main_effort`에 group id 대신 문장("G1이 주력이다…")을 쓴 형식 오류다. 예시가 있으면(DF) 이 오류는 사라지지만, 예시만 준 F보다 나아지지도 않는다. 교범 3이 검색으로 고른 것이라 품질이 낮고, 방책 수립 절차(상대 전투력, 시간·거리, 결심점)가 빠진 것이 원인으로 보인다.
3. **배치 판단은 실제 지휘관과 여전히 다르다.** 부대별 배치 거리가 모든 조건에서 1.5~1.6km다. 모든 부대를 GT 배치 중심에 둔 기준선(1.73km)보다 조금 나을 뿐이다. 형식과 관행은 예시에서 배우지만, 어디에 무엇을 둘지는 잘 옮겨 오지 못한다.
4. **심사 점수로 "좋은 COA"를 말할 수는 없다.** GT의 심사 점수는 실제 결과와 반대로 움직였다(성공 5.16, 부분 성공 5.53, 실패 5.60). 심사는 교범적 완성도를 보고 결과를 예측하지 않는다. 품질의 최종 판단은 시뮬레이션 결과로 한다.

**다음 실험 (DF+)**

- 교범 3을 사람이 고른 조항으로 바꾼다.
- 교범 4(방책 수립 절차: FM 5-0 5-74~5-101, ATP 5-0.2-1 표 2-12·D-4, FM 3-90 8-52)를 더한다.
- 그 조항에서 파생한 분석(축선별 전투력 비, 이동·도달 시간)은 코드가 계산해서 넣고, 점검표도 함께 준다.
- `main_effort`는 group id만 받도록 고친다.
