# Pseudo-COA

6·25전쟁 연대급 전투 50건으로 만든 **COA(방책) 생성·시뮬레이션용 데이터셋과 도구**입니다.

전투마다 세 가지가 있습니다.
- 지휘관이 명령을 내리던 순간의 **상황**
- 그때 실제로 내린 **명령**(pseudo-GT COA)
- 적의 실제 계획과 실제 경과

생성 모델에 상황을 주고 COA를 만들게 한 뒤, pysc2 시뮬레이터에서 같은 적과 싸워 보게 하는 데 씁니다.

```
  상황 ─────▶ [COA 생성 모델] ──▶ 새 COA ──▶ [검사] ──▶ [pysc2 시뮬레이터] ──▶ 결과 ──▶ 실제 경과와 비교
situation.json      ▲                                        ▲                              history.json
             pseudo-GT 예시 + 교범                        scenario.json
             coa.json    doctrine/                        (적 계획·환경)
```

## 어디서 시작하나요

| 이런 분은 | 먼저 볼 것 |
|---|---|
| 처음 오신 분 | [튜토리얼](docs/tutorial/README.md) (`python3 docs/tutorial/tutorial.py`, 30분) → 아무 사례 폴더나 열어 보기 (예: [`cases/kb2_023/`](cases/kb2_023)) |
| **시뮬레이터를 만드는 분** | [시뮬레이션 방법](docs/simulation/how_to_simulate.md) → [사례 따라가기: 백마고지](docs/simulation/walkthrough_kb2_023.md) → [정해야 할 것들](docs/simulation/decisions_needed.md) |
| **COA를 생성하는 분** | [COA 생성](docs/generation/how_to_generate.md) → [교범 묶음](doctrine/README.md) → [생성 품질 실험](experiments/2026-10-19_fewshot/README.md) |
| 필드 정의를 찾는 분 | [JSON 필드 사전](docs/reference/json_fields.md), [열거값 사전](docs/reference/vocabulary.md), [`schema/`](schema) |

## 무엇이 들어 있나요

```
Pseudo-COA/
├── cases/                    사례 50건. 사례 하나 = 폴더 하나
│   ├── cases.csv             전체 목록 (임무 유형, 실제 결과, 보정용 여부 …)
│   └── kb2_023/
│       ├── README.md         사례 요약 · 약도 · 명령서 (GitHub에서 폴더를 열면 보인다)
│       ├── situation.json    ① 상황              생성 모델 ○   시뮬레이터 ○
│       ├── coa.json          ② pseudo-GT COA     예시로 ○      시뮬레이터 ○ (새 COA로 바꿔 끼움)
│       ├── scenario.json     ③ 적 계획·환경       생성 모델 ✗   시뮬레이터 ○
│       ├── history.json      ④ 실제 경과          생성 모델 ✗   시뮬레이터 ✗ (평가에만)
│       ├── source.json       출처 · 결과 라벨 · 축척 · 자동 검사
│       ├── real_names/       ①②의 실명판 (사람 검토용)
│       └── map.svg
├── doctrine/                 생성 모델 입력에 넣는 교범 조항 (미 육군 공개 교범)
├── pseudo_coa/               코드 (표준 라이브러리만): 사례 읽기 · 검사 · 시뮬레이터 입력 · 생성
├── schema/                   블록별 JSON Schema (situation / coa / scenario / history / source)
├── docs/
│   ├── tutorial/             JSON 양식 튜토리얼
│   ├── simulation/           시뮬레이터를 만드는 사람용
│   ├── generation/           COA를 생성하는 사람용
│   └── reference/            필드 사전, 열거값 사전
├── experiments/              실험과 결과 (날짜별)
└── sim_unit_table.json       부대 규모 → SC2 유닛 수 환산표 (보정 전 초안)
```

## 5분 시작

Python 3.8 이상이면 설치 없이 레포 최상위에서 돌아갑니다. 모델 호출(`generate`)에만 Claude Code CLI 로그인이나 OpenAI 호환 서버가 필요합니다.

```bash
python -m pseudo_coa list                                  # 사례 목록
python -m pseudo_coa show kb2_023                          # 사례 하나 요약
python -m pseudo_coa validate --all                        # pseudo-GT 50건 검사 → 통과 50 / 50

# 시뮬레이터 입력: 상황 + COA + 시나리오 (history는 넣지 않는다)
python -m pseudo_coa sim-input kb2_023 -o sim.json                       # pseudo-GT COA로
python -m pseudo_coa sim-input kb2_023 --coa my_coa.json -o sim.json     # 새 COA로 (검사를 통과해야 만든다)
python -m pseudo_coa eval-target kb2_023 -o eval.json                    # 평가 기준 (시뮬레이션이 끝난 뒤에만)

# COA 생성
python -m pseudo_coa prompt kb2_023 --cond DF              # 프롬프트만 보기 (모델 호출 없음)
python -m pseudo_coa generate kb2_023 --out my_coa.json    # 생성 → 검사
```

파이썬에서는 다음과 같습니다.

```python
from pseudo_coa import load_case, validate

c = load_case("kb2_023")
c.situation, c.coa, c.scenario, c.history, c.meta    # 블록
errors, warnings = validate(c, my_order)             # 새 COA 검사
sim = c.sim_input(my_order)                          # 시뮬레이터 입력
```

## 꼭 지킬 규칙 세 가지

1. **새 COA가 바꾸는 것은 `coa.json`(order 블록) 하나뿐입니다.** 상황과 시나리오는 사례마다 고정입니다.
2. **생성 모델에는 `situation.json`과 (예시로) `coa.json`만 줍니다.** `scenario.json`에는 연대가 몰랐던 적이, `history.json`에는 실제 결과가 있습니다. `history.json`은 시뮬레이터에도 주지 않습니다.
3. **조건은 전투력으로만 씁니다.** 예비 투입과 적의 반응은 "어느 부대 손실이 몇 %를 넘으면"(`losses_exceed`)이나 "어느 지역에 적이 어느 규모 이상 있으면"(`strength_in_area`)으로만 씁니다. 시각(`time_elapsed`)은 조건이 아니라 일정입니다. 결과는 시뮬레이터가 내야 하기 때문입니다.

## 용어

| 용어 | 뜻 |
|---|---|
| COA | Course of Action, 방책. 여기서는 연대장의 **초기 배치 작전명령** 하나(`order` 블록)로 표현합니다 |
| pseudo-GT | 그 연대가 실제로 내린 명령을 전쟁사 서술에서 재구성한 것. 정답(최적해)이 아니라 **현실의 기준선**입니다. 실제 결과는 성공·부분 성공·실패가 섞여 있습니다 |
| 상황 | 명령 시점에 연대가 알던 것: 상급 임무·의도, 작전지역, 가용 부대(F1…), 지형(H395…), 적(E1…) |
| 시나리오 | 시뮬레이터만 받는 것: 적의 실제 계획과 반응 규칙, 숨은 적(HE1…), 야간·안개 같은 환경, 시작·끝 시각 |
| 실제 경과 | 실제로 일어난 일. 시뮬레이션 결과와 비교하는 데만 씁니다 |
| `t` | D일 00:00부터 지난 시간(h). D+1일 06:00 = 30 |
| 좌표 | 200×200 캔버스, 1단위 = 100m, 북쪽이 +y |
| 익명화 | 지명·부대명·날짜를 별칭으로 바꾼 것(`395고지` → `고지 A`). id와 좌표는 그대로입니다 |
| 보정용 (`calibration_ok`) | 시뮬레이터 보정 기준선에 써도 되는 사례(30건). 나머지 20건은 시나리오에 실제 결과가 섞였을 수 있습니다 |

## 데이터 개요

| 항목 | 값 |
|---|---|
| 사례 | 50건 (육군 49, 해병대 1). 출처: 국방부 군사편찬연구소 『6·25전쟁 주요전투』 1·2권 |
| 관점 | 연대 (전투 구간 시작 때 그 지역을 맡은 연대) |
| 임무 유형 | 지역방어 23 · 공격 14 · 역습 11 · 지연 2 |
| 실제 결과 | 성공 25 · 부분 성공 15 · 실패 10 |
| 시뮬레이션 길이 | 15~150시간, 평균 69시간 |
| 규모 | 아군 과업 단위 207개, 적 행동 항목 646개, 지형지물 741개 |
| 만든 방법 | 전쟁사 서술 → claude-opus-5-5 두 단계 생성 → 규칙 검사 + 의미 검사(claude-sonnet-5) |

## 알아 둘 한계

- **좌표는 대부분 추정입니다.** 지형지물 741개 중 703개가 서술에서 추정한 위치입니다. 상대 위치는 맞지만 수백 m 단위의 정밀도는 기대하지 않습니다.
- **유닛 환산표는 보정 전 초안입니다.** pseudo-GT를 돌려 실제 결과가 재현되도록 맞추는 것이 첫 작업입니다([시뮬레이션 방법 §7](docs/simulation/how_to_simulate.md#7-종료와-평가)).
- **pseudo-GT는 사람이 전부 검토하지 않았습니다.** 검토한 것은 3건(kb2_023, kb1_062, kb1_189)과 kb2_006 일부입니다(`cases.csv`의 `human_reviewed`). 자동 의미 검사가 지적한 49개 항목(29건)도 확인 전입니다.
- **`history`의 손실률은 약 40건에만 있습니다.**

## 문의와 수정 요청

틀리거나 부족한 곳은 사례 id와 JSON 경로(예: `kb2_023 scenario.enemy_plan.groups[6].items[2]`)를 적어 알려 줍니다. 바뀐 내용은 [CHANGELOG](CHANGELOG.md)에 남깁니다.
