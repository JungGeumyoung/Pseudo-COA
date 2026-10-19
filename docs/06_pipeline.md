# 06. COA 생성 파이프라인

situation 하나에서 COA(order)를 생성해 시뮬레이터 입력으로 만들기까지의 흐름이다. 코드는 `pipeline/`에 있다.

```
 data/inputs/<id>.json ─┐  situation (익명화 input)
 doctrine/doctrine_pack.json ─┤  교범: 동사 정의 + 임무 유형별 조항          (조건 D, DF)
 data/anon/*.json ──────┤  pseudo-GT 예시 k건 {input → order}         (조건 F, DF)
                        ▼
              pipeline/prompt.py   system(명령 규칙) + user
                        ▼
              pipeline/backends.py  생성 모델 (구조화 출력: schema/order.schema.json)
                        ▼
              tools/validate_order.py   오류 0이어야 통과
                        ▼
              tools/case_io.py sim_view  input + 새 order + scenario  ──▶  pysc2
```

## 실행

```bash
# 프롬프트만 보기 (모델 없이)
python3 pipeline/generate_coa.py --case kb2_023 --dry-run > prompt.txt

# 50건 중 하나로 생성 → 검사 → 시뮬레이터 입력
python3 pipeline/generate_coa.py --case kb2_023 --out runs/kb2_023.json --sim-out runs/kb2_023.sim.json

# 새 상황 (input 블록 꼴 JSON. 시뮬레이터 입력은 scenario가 있어야 만들 수 있다)
python3 pipeline/generate_coa.py --situation my_situation.json --mission-type 지역방어 --out runs/new.json
```

| 옵션 | 기본값 | 뜻 |
|---|---|---|
| `--cond` | `DF` | `Z` situation만 / `D` +교범 / `F` +예시 / `DF` +교범+예시 |
| `--k` | 3 | 예시 수 |
| `--backend` | `claude:claude-sonnet-5-5:medium` | `claude:<model>:<effort>`(Claude Code CLI, 로그인 필요) 또는 `openai:<base_url>\|<model>`(vLLM·Ollama 등 OpenAI 호환 서버, `openai` 패키지 필요) |

결과 JSON은 `{id, mission_type, cond, examples, order, validation: {ok, errors, warnings}, gen}`이다. 종료 코드는 검사 오류가 없으면 0이다.

## 프롬프트 구성 (`pipeline/prompt.py`)

- **system** (`GEN_SYSTEM`, 약 3천 자): 명령의 형태, 전투편성, 과업 동사 32개와 동사별 필수 params, timing, 전투력 조건, 참조·좌표 규칙. 사례 생성기(데이터 구축용)의 규칙 가운데 order에 해당하는 것만 옮겼다.
- **user**: 아래 순서로 붙인다.
  1. (D) 교범 1: 과업 동사의 교범 정의 32개 조항. 교범 2: 그 임무 유형의 조항 8개.
  2. (F) 예시 k건: `[situation]` + `[order]` JSON. 공백 없이 압축해서 넣는다.
  3. 이번 과제: `[situation]` JSON
- **예시 고르기** (`pick_examples`): 같은 임무 유형을 먼저 고른다. 그 안에서는 가용 부대 수 차이 + 0.5 × 적 부대 수 차이가 작은 순으로 고른다. 50건 안의 사례가 대상이면 그 사례와 **같은 전투**는 예시에서 뺀다(leave-one-out). 같은 전투는 제목의 지명이나 고지 번호가 겹치는 경우다. 예: 351고지 전투 kb2_019 ↔ kb2_029.
- 프롬프트 길이(kb2_023): Z 1만 / D 4만 / F 5.7만 / DF 8.7만 자.

## 생성 모델을 바꿀 때

`pipeline/backends.py`의 `generate(system, user, schema) -> (obj, meta)`를 같은 서명으로 구현하면 된다. 구조화 출력을 지원하지 않는 모델이면 응답에서 첫 JSON 객체를 꺼낸다(`_extract_json`). 출력 order는 약 8KB다. 출력 한도가 작은 모델은 잘릴 수 있다.

## 생성 품질 실험 (`pipeline/experiment/`)

few-shot으로 쓸 만한 COA가 나오는지 시뮬레이터 없이 먼저 본 실험이다. 50건 모두를 leave-one-out으로 돌렸고, 조건은 Z / D / F / DF 네 가지다.

```bash
python3 pipeline/experiment/run_gen.py --model claude-sonnet-5-5 --workers 4   # 200건 생성 → results/gen/<cond>/<id>.json
python3 pipeline/experiment/score.py                                           # 규칙 검사 + GT 구조 일치 → results/scores.jsonl
python3 pipeline/experiment/judge.py --model claude-opus-5-5 --workers 4       # LLM 블라인드 심사 (GT 포함) → results/judge/
python3 pipeline/experiment/report.py                                          # → results/REPORT.md
```

평가는 세 층이다.

1. **규칙 검사**: `validate_order` 오류가 0인 비율. 시뮬레이터에 바로 넣을 수 있는가를 본다.
2. **pseudo-GT와의 구조 일치**: 부대별 배치 거리(km), 주력·예비 구성 일치(Jaccard), 예비 투입 조건 일치, 핵심 지형·과업 목표 지형 일치, 임무 동사 일치. GT는 역사적 재구성이지 최적해가 아니다. 그래서 이 값은 "실제 지휘관과 얼마나 비슷하게 판단했나"를 뜻하고 "얼마나 좋은가"를 뜻하지 않는다.
3. **LLM 심사**: 심사 모델은 situation과 order 하나만 보고 다섯 항목(임무 부합, 지형 활용, 적 대응, 전투력 운용, 협조·실행성)을 1~5점으로, 전체를 1~10점으로 매긴다. GT order도 같은 프롬프트로 출처를 숨기고 채점해 기준선으로 쓴다.

최종 판단은 시뮬레이션이다. 같은 scenario에서 생성 COA와 GT COA를 돌려 결과(`history.outcome_metrics` 꼴)를 비교한다. 실험 결과는 생성·심사가 끝나는 대로 이 문서와 `pipeline/experiment/results/`에 더한다.
