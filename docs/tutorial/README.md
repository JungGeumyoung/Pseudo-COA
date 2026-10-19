# 튜토리얼: JSON 양식 익히기

사례 하나(kb2_023 백마고지)를 직접 열어 보며 양식을 익힙니다. 30분이면 됩니다. 각 단계는 `tutorial.py`의 함수 하나입니다. 출력을 보면서 이 문서의 설명을 읽습니다.

```bash
python3 docs/tutorial/tutorial.py        # 1~9단계 전부 (레포 최상위에서)
python3 docs/tutorial/tutorial.py 3 4    # 3, 4단계만
```

| 단계 | 내용 | 더 읽을 곳 |
|---|---|---|
| 1 | 사례 폴더 `cases/<id>/`의 파일들 | [cases/README](../../cases/README.md) |
| 2 | `input`: 생성 모델이 받는 상황 | [§input](../reference/json_fields.md) |
| 3 | `order`: 생성 모델이 쓰는 COA | [§order](../reference/json_fields.md) |
| 4 | 조건과 timing | [§4](../simulation/how_to_simulate.md) |
| 5 | `scenario`: 시뮬레이터만 받는 것 | [§5–6](../simulation/how_to_simulate.md) |
| 6 | `history`: 평가에만 쓰는 것 | [§7](../simulation/how_to_simulate.md) |
| 7 | 유닛 환산 | [§3](../simulation/how_to_simulate.md), `sim_unit_table.json` |
| 8 | 검사: 잘못된 order가 어떻게 걸리는가 | `python -m pseudo_coa validate` |
| 9 | 생성 → 검사 → 시뮬레이터 입력 | [COA 생성](../generation/how_to_generate.md) |

## 1. 사례 폴더

사례 하나는 `cases/<id>/` 폴더 하나이고, 블록마다 파일이 하나씩입니다. **파일 이름만 보고 누구에게 줘도 되는지 알 수 있게** 나눴습니다.

| 파일 | 블록 | 생성 모델 | 시뮬레이터 |
|---|---|---|---|
| `situation.json` | `input`: 상황 (익명화) | ○ 입력 | ○ |
| `coa.json` | `order`: pseudo-GT COA (익명화) | ○ 예시로만 | ○ (또는 새 COA로 바꿔 끼움) |
| `scenario.json` | `scenario`: 적 계획, 숨은 적, 환경 | ✗ | ○ |
| `history.json` | `history`: 실제 경과 | ✗ | ✗ (평가에만) |
| `source.json` | `meta`, `checks`: 출처, 결과 라벨, 축척, 자동 검사 | ✗ | 축척만 |
| `real_names/` | `input`, `order`의 실명판 | ✗ | (필요 없음, id·좌표가 같음) |
| `README.md`, `map.svg` | 사람이 읽는 사례 요약·명령서와 약도 | | |

익명화는 이름만 바꿉니다(`395고지` → `고지 A`, `제30연대` → `아군 연대`). id와 좌표는 실명판과 같습니다. 파이썬에서는 `load_case("kb2_023")`의 속성(`.situation`, `.coa`, `.scenario`, `.history`, `.meta`)으로 읽습니다.

## 2. input

명령 시점에 연대가 알았던 것만 있습니다. 모든 대상에는 id가 있고, order는 이 id로 대상을 가리킵니다.

- `available_forces[]`(F1, F2…): 전투편성의 재료입니다. `echelon`·`type`·`modifier`·`strength_pct`로 규모를 정형화했습니다.
- `terrain.features[]`(H395 등): 과업의 목표·지역입니다. 좌표는 200×200 캔버스이고 1단위는 100m, 북쪽이 +y입니다.
- `enemy_forces[]`(E1…): 연대가 알던 적입니다. 몰랐던 적은 `scenario.hidden_enemy`에 있습니다.
- `higher_context.higher_rules[]`: 상급·인접 부대의 조건부 행동입니다. 예를 들어 사단 예비의 역습입니다. 연대의 명령이 아니어도 시뮬레이터가 실행합니다.

## 3. order

명령서 번호를 그대로 따릅니다.

| 명령서 | 키 |
|---|---|
| 전투편성 | `task_organization` |
| 1. 상황 | `situation` |
| 2. 임무 | `mission` |
| 3. 실시 | `execution`: `end_state`, `concept`, `tasks`, `coordinating` |

시뮬레이터가 실제로 읽는 것은 다음 다섯 가지입니다. 나머지 문장 필드는 사람이 읽거나 심사하는 데 씁니다.

- `task_organization.groups[]`: 어떤 F를 묶어 G를 만들었는지 나타냅니다. `part`로 중대를 붙이거나 뗍니다.
- `tasks[].deploy`: G의 최초 위치, 정면, 다각형, 중대 위치
- `tasks[].items[]`: `timing` + `verb` + `params` (+ `trigger`)
- `concept.reserve.commit`: 예비 투입 조건
- `coordinating.control_measures[]`: order 안에서 정의하는 CM_* id(교전지역, 역습로 등)

## 4. 조건과 timing

| 누구 | timing 값 |
|---|---|
| 아군 과업 | `즉시` / `이어서`(같은 G의 앞 항목이 끝나면) / `명에 의해`(trigger가 참이 되면) |
| 적 계획 | `계획`(start 시각) / `이어서` / `조건` |
| 상급 규칙 | `계획` / `조건` |

반응 조건은 **전투력 두 가지뿐**입니다.

- `losses_exceed`: 부대의 누적 손실 비율이 문턱을 넘음
- `strength_in_area`: 어떤 지역 안에 일정 규모 이상의 부대가 있음

시각(`time_elapsed`, D일 00:00부터 경과한 시간)은 조건이 아니라 일정입니다. 결과("고지를 잃으면")를 조건으로 쓰지 않는 이유는 결과를 시뮬레이터가 내야 하기 때문입니다.

## 5–6. scenario와 history

- `scenario`: 적의 실제 계획(`enemy_plan`), 숨은 적, 외생 사건(야간·안개·범람), 조기 종료 조건, 시작 시각(`start_t`)과 시뮬레이션 시간(`horizon_h`). 생성 모델은 보지 못합니다.
- `history`: 실제 경과와 끝 시각의 상태(`outcome_metrics`)입니다. **시뮬레이터에 넣지 않습니다.** 시뮬레이션 결과와 비교하는 데만 씁니다.

## 7. 유닛 환산

`sim_unit_table.json`이 제대를 SC2 유닛 수로 바꿉니다. 기준은 유닛 1개 = 보병 소대 1개입니다. 보병 대대는 보병 9 + 화기 5 + 박격포 1입니다. 표는 pseudo-GT를 돌려서 실제 결과가 재현되도록 보정해야 하는 초안입니다.

## 8. 검사

`python -m pseudo_coa validate <id> <coa.json>`(파이썬에서는 `validate(id, order)`)은 order가 그 사례에 들어갈 수 있는지 검사합니다. 오류가 하나라도 있으면 시뮬레이션하지 않습니다. 튜토리얼은 pseudo-GT를 일부러 네 군데 망가뜨려서 오류 네 개가 나오는 것을 보여 줍니다.

- 정의되지 않은 id
- `즉시` 과업에 trigger
- 시각을 조건으로 씀
- 역습에 `route`가 없음

## 9. 파이프라인

```bash
python -m pseudo_coa prompt kb2_023 --cond DF | less                                 # 프롬프트 보기 (모델 없이)
python -m pseudo_coa generate kb2_023 --out runs/kb2_023.json --sim-out runs/kb2_023.sim.json
```

`runs/kb2_023.sim.json`이 시뮬레이터 입력입니다. 사례의 `input`·`scenario`는 그대로이고 `order`만 새 COA로 바뀝니다. 자세한 내용은 [COA 생성](../generation/how_to_generate.md)에 있습니다.
