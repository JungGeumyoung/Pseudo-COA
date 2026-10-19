# COA 생성

상황 하나에서 COA(`order` 블록)를 생성해 검사하고 시뮬레이터 입력으로 만들기까지의 흐름입니다. 코드는 [`pseudo_coa/generate/`](../../pseudo_coa/generate)에 있습니다.

```
 cases/<id>/situation.json ─────┐  상황 (익명화)
 doctrine/doctrine_pack.json ───┤  교범: 동사 정의 + 명령 구성 요소 + 임무 유형별 조항   (조건 D, DF)
 cases/<다른 id>/situation.json ┤  pseudo-GT 예시 k건: 상황 → coa                       (조건 F, DF)
   + coa.json                   │
                                ▼
                 pseudo_coa/generate/prompt.py    system(명령 규칙) + user
                                ▼
                 pseudo_coa/generate/backends.py  생성 모델 (구조화 출력: schema/coa.schema.json)
                                ▼
                 pseudo_coa/validate.py           오류 0이어야 통과
                                ▼
                 Case.sim_input(order)            상황 + 새 COA + scenario  ──▶  pysc2
```

## 실행

```bash
# 프롬프트만 보기 (모델 호출 없음)
python -m pseudo_coa prompt kb2_023 --cond DF > prompt.txt

# 50건 중 하나로 생성 → 검사 → (통과하면) 시뮬레이터 입력
python -m pseudo_coa generate kb2_023 --out runs/kb2_023.json --sim-out runs/kb2_023.sim.json

# 새 상황 (input 블록 꼴 JSON. scenario가 없으므로 시뮬레이터 입력은 만들지 않는다)
python -m pseudo_coa generate --situation my_situation.json --mission-type 지역방어 --out runs/new.json
```

| 옵션 | 기본값 | 뜻 |
|---|---|---|
| `--cond` | `DF` | `Z` 규칙만 / `D` +교범 / `F` +예시 / `DF` +교범+예시 |
| `-k` | 3 | 예시 수 |
| `--backend` | `claude:claude-sonnet-5-5:medium` | `claude:<model>:<effort>`(Claude Code CLI, 로그인 필요) 또는 `openai:<base_url>\|<model>`(vLLM·Ollama 등 OpenAI 호환 서버, `openai` 패키지 필요) |

결과 JSON은 `{id, cond, examples, order, validation: {ok, errors, warnings}, gen}`입니다. 검사 오류가 없으면 종료 코드 0입니다.

파이썬에서는 다음과 같습니다.

```python
from pseudo_coa import load_case, validate
from pseudo_coa.generate import build_prompt, generate_coa

system, user, examples = build_prompt("kb2_023", cond="DF")      # 모델 없이
order, meta = generate_coa("kb2_023", cond="DF")                  # 생성
errors, warnings = validate("kb2_023", order)
sim = load_case("kb2_023").sim_input(order)                       # 시뮬레이터 입력
```

## 프롬프트 구성 (`pseudo_coa/generate/prompt.py`)

- **system** (`GEN_SYSTEM`, 약 3천 자): 명령의 형태, 전투편성, 과업 동사 32개와 동사별 필수 params, timing, 전투력 조건, 참조·좌표 규칙. 데이터를 만들 때 쓴 규칙 가운데 `order`에 해당하는 것만 옮겼습니다.
- **user**: 아래 순서로 붙입니다.
  1. (D) 교범 1: 과업 동사의 교범 정의 32개 조항. 교범 2: 명령의 구성 요소 16개 조항(임무 문장, 의도, 작전개념, 가정, 예비). 교범 3: 그 임무 유형의 조항 8개. 자세한 내용은 [`doctrine/`](../../doctrine)에 있습니다.
  2. (F) 예시 k건: `[situation]` + `[order]` JSON. 공백 없이 압축해서 넣습니다.
  3. 이번 과제: `[situation]` JSON
- **예시 고르기** (`pick_examples`): 같은 임무 유형을 먼저 고릅니다. 그 안에서는 가용 부대 수 차이 + 0.5 × 적 부대 수 차이가 작은 순으로 고릅니다. 50건 안의 사례가 대상이면 그 사례와 **같은 전투**는 예시에서 뺍니다(leave-one-out). 같은 전투는 제목의 지명이나 고지 번호가 겹치는 경우입니다. 예: 351고지 전투 kb2_019 ↔ kb2_029.
- 프롬프트 길이(kb2_023, system 포함): Z 1.0만 / D 5.2만 / F 5.7만 / DF 9.8만 자.

## 생성 모델을 바꿀 때

`pseudo_coa/generate/backends.py`의 `generate(system, user, schema) -> (obj, meta)`를 같은 서명으로 구현해 `generate_coa(..., backend=객체)`로 넘기면 됩니다. 구조화 출력을 지원하지 않는 모델이면 응답에서 첫 JSON 객체를 꺼냅니다(`_extract_json`). 출력 order는 약 8KB라 출력 한도가 작은 모델은 잘릴 수 있습니다.

## 생성 품질

교범과 pseudo-GT 예시가 도움이 되는지 본 실험(2026-10-19)은 [`experiments/2026-10-19_fewshot/`](../../experiments/2026-10-19_fewshot)에 있습니다. 요약은 다음과 같습니다.

- **예시(few-shot)는 효과가 있습니다.** 심사 점수가 0.3점 올라 GT와 같은 수준이 되고, 조건 쓰는 법과 동사 선택이 GT에 가까워집니다.
- **지금 교범 묶음은 효과가 거의 없습니다.** 교범만 주면 형식 오류가 늘고, 예시가 있을 때 더해도 나아지지 않습니다.
- **배치 판단은 실제 지휘관과 여전히 다릅니다.**
- **심사 점수는 실제 결과를 예측하지 못했습니다.** 최종 판단은 시뮬레이션으로 합니다.
