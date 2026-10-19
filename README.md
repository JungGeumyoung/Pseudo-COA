# COA 시뮬레이션 데이터셋 `reduced-opord/0.6`

6·25전쟁 연대급 전투 **50건**을 시뮬레이터가 읽을 수 있는 **축약 작전명령(OPORD)** 꼴로 정리한 데이터셋이다. 사례마다 네 가지가 있다. 명령 시점의 상황, 그 연대가 실제로 내린 초기 배치 명령(모범 답안), 적의 계획과 환경, 실제 경과다.

쓰임은 둘이다.
1. **few-shot 예시**: 생성 모델이 처음 보는 상황에서 COA(방책)를 명령 꼴로 만들 때 예시로 쓴다.
2. **시뮬레이션 시나리오**: 그렇게 만든 COA를 pysc2에서 같은 상황, 같은 적 계획으로 돌려 모범 답안·실제 결과와 비교한다.

```
                    ┌──────────── few-shot 예시: data/anon/*.json 의 {input → order} ────────────┐
                    ▼                                                                            │
 data/anon/<id>.json  input (익명화)  ──▶  생성 모델  ──▶  새 order  ──▶  tools/validate_order.py
                                                                              │ 통과
 data/cases/<id>.json  input + scenario ──────────────────────────────────────┤
                                                                              ▼
                                                         tools/case_io.py sim  ──▶  pysc2 시뮬레이터
                                                                                          │ 결과
 data/cases/<id>.json  history ──▶ tools/case_io.py eval ──────────────▶  평가: 실제 결과·모범 답안 결과와 비교
```

> **핵심 규칙 세 가지**
> 1. 새 COA가 대신하는 것은 **`order` 블록 하나**다. `input`과 `scenario`는 사례마다 고정이다.
> 2. **`history`는 시뮬레이터에 주지 않는다.** 평가와 보정에만 쓴다. 데이터에는 결정만 있고 결과는 시뮬레이터가 낸다.
> 3. 반응 조건은 **전투력 조건 두 가지**(`losses_exceed`, `strength_in_area`)뿐이다. 시각(`time_elapsed`)은 조건이 아니라 일정이다.

---

## 빠른 시작

표준 라이브러리만 쓴다(Python 3.8+).

```bash
# 1) 모범 답안 50건이 검사를 통과하는지 확인
python3 tools/validate_order.py --all                     # 통과 50 / 50

# 2) 사례 하나를 시뮬레이터 입력과 평가 기준으로 나누기
python3 tools/case_io.py sim  data/cases/kb2_023.json > sim_input.json    # input + order + scenario
python3 tools/case_io.py eval data/cases/kb2_023.json > eval_target.json  # history (평가 전용)

# 3) 생성 모델이 받을 입력(익명화본)
python3 tools/case_io.py prompt data/cases/kb2_023.json > given.json

# 4) 새로 생성한 COA를 검사하고 시뮬레이터 입력으로 만들기
python3 tools/validate_order.py data/cases/kb2_023.json new_order.json    # 오류가 없어야 한다
python3 tools/case_io.py sim data/cases/kb2_023.json --order new_order.json > sim_input.json
```

처음이라면 [03. 사례 따라가기](docs/03_walkthrough_kb2_023.md)부터 읽는다. 백마고지 사례 하나로 전체 구조를 볼 수 있다.

## 폴더 구조

```
Pseudo-COA/
├── README.md                     ← 이 문서
├── CHANGELOG.md                  스키마 버전 이력 (0.4 → 0.5 → 0.6)
├── docs/
│   ├── 01_schema.md              필드 레퍼런스: 블록별 키, 타입, 필수 여부, 시뮬레이터가 읽는지
│   ├── 02_simulator_contract.md  시뮬레이터 계약: 읽는 순서, 유닛 환산, 사건 판정, 규칙 실행, 종료·평가
│   ├── 03_walkthrough_kb2_023.md 사례 하나를 처음부터 끝까지 (백마고지)
│   ├── 04_vocabulary.md          열거값 사전: 동사, mode, kind 등과 50건의 실제 빈도
│   └── 05_open_questions.md      시뮬레이션 팀이 정해야 할 것 (Q1~Q16)
├── schema/
│   ├── reduced-opord-0.6.schema.json   사례 파일 전체의 JSON Schema
│   └── order.schema.json               order 블록만 (생성 모델의 구조화 출력에 그대로 쓸 수 있다)
├── sim_unit_table.json           부대 규모 → 시뮬레이션 유닛 수, SC2 유닛 매핑 제안, 초기 계수 (보정 대상 초안)
├── data/
│   ├── cases/<id>.json           사례 50건 전체 (meta, input, order, scenario, history, checks)
│   ├── anon/<id>.json            익명화본 (input, order만). 생성 모델에 주는 것
│   ├── index.jsonl               사례당 한 줄 요약
│   └── CASES.md                  사례 목록과 품질 표시
├── examples/
│   ├── <id>.order.md             명령서 문장 (사람이 읽는 꼴), 50건
│   └── <id>.map.svg              좌표로 그린 약도, 50건
└── tools/
    ├── case_io.py                사례 → sim / eval / prompt 뷰
    └── validate_order.py         새 order 검사기 (구조 + 참조 + 동사·조건 규칙)
```

## 데이터셋 개요

| 항목 | 값 |
|---|---|
| 사례 수 | 50 (육군 49, 해병대 1) |
| 출처 | 국방부 군사편찬연구소 『6·25전쟁 주요전투』 1·2권 |
| 관점 | 연대 (전투 구간 시작 때 그 지역의 작전지역을 맡은 연대) |
| 범주 | 고지 방어·탈환 33 · 능선 공격 9 · 하천선 방어·방어 후 역습 6 · 지연·철수·사주방어 2 |
| 임무 유형 | 지역방어 23 · 공격 14 · 역습 11 · 지연 2 |
| 실제 결과 | success 25 · partial 15 · failure 10 |
| 시뮬레이션 길이 | 15~150시간, 평균 69시간 |
| 좌표 | 200×200 캔버스, 1단위 = 100m. 아틀라스 측정 3건, 나머지는 서술 추정 |
| 규모 | 아군 과업 단위 207개, 적 행동 항목 646개, 지형지물 741개 |
| 생성 | claude-opus-5-5 두 단계 생성 + 규칙 검사 + 의미 검사(claude-sonnet-5) |

사례별 정보는 [`data/CASES.md`](data/CASES.md)에 있다.

## 사례 파일 한눈에 보기

```jsonc
{
  "schema": "reduced-opord/0.6",
  "id": "kb2_023",
  "meta":     { … },   // 출처, 구간, 결과 라벨, 축척. 시뮬레이터는 meta.geo.scale_m_per_unit만 읽는다
  "input": {           // 명령 시점에 연대가 알던 것 — 생성 모델 입력(익명화본), 시뮬레이터 입력
    "perspective", "higher_context" (상급 임무, 인접 부대, 상급 규칙 higher_rules),
    "area_of_operations", "available_forces" (F*), "terrain" (features·routes·impassable),
    "enemy_forces" (E*), "conditions"
  },
  "order": {           // 연대의 초기 배치 명령 — 모범 답안. 새 COA가 이 블록을 대신한다
    "task_organization" (G*), "situation", "mission",
    "execution": { "end_state", "concept" (주력·예비·화력), "tasks" (배치 + 과업 목록), "coordinating" (시간계획·통제수단 CM*) }
  },
  "scenario": {        // 시뮬레이터 전용 — 적 실제 계획, 숨은 적 HE*, 외생 사건, 시간
    "start_t", "horizon_h", "stop_conditions", "enemy_plan", "hidden_enemy", "exogenous"
  },
  "history":  { … },   // 평가 전용 — 실제 경과, outcome_metrics(끝 시각의 실제 상태)
  "checks":   { … }    // 생성 뒤 붙인 규칙 검사 결과
}
```

자세한 필드는 [01. 스키마 레퍼런스](docs/01_schema.md)에 있다.

### 과업과 조건은 이렇게 생겼다

```jsonc
// order.execution.tasks[] — 예비 group G3
{ "group": "G3",
  "deploy": { "kind": "예비진지", "xy": [126.6, 62.2], "preparation": "hasty", … },
  "items": [
    { "timing": "즉시",      "verb": "점령", "params": { "objective": "CM_AA" }, … },
    { "timing": "명에 의해", "verb": "역습", "params": { "objective": "H395", "route": "CM_RT" },
      "trigger": { "type": "strength_in_area", "side": "enemy", "ref": "H395", "min_echelon": "중대",
                   "text": "적 중대 이상이 395고지 주봉 지역 안에 있음" },
      "basis": "risk_point: …" } ] }

// scenario.enemy_plan.groups[] — 적 대대 E2
{ "group": "E2", "items": [
    { "timing": "계획", "mode": "attack", "objective_ref": "H395",
      "start": { "type": "time_elapsed", "value": 19.25, "text": "D일 19:15" },
      "repeat": { "max": 3, "interval_h": 2.7 }, … },
    { "timing": "조건", "mode": "hold", "objective_ref": "H_NM",
      "trigger": { "type": "strength_in_area", "side": "enemy", "ref": "H_NM", "min_echelon": "중대", … }, … } ] }
```

| timing | 아군 | 적 | 상급·인접 | 시작 |
|---|---|---|---|---|
| 즉시 | ● | | | 시뮬레이션 시작 때 |
| 계획 | | ● | ● | 정해진 시각(`time_elapsed`) |
| 이어서 | ● | ● | | 같은 목록의 바로 앞 항목이 끝났을 때 |
| 명에 의해 / 조건 | ● | ● | ● | 전투력 조건이 참이 될 때 |

| 조건 type | 필드 | 참이 되는 때 |
|---|---|---|
| `losses_exceed` | `group`, `fraction` | 그 부대의 누적 손실 비율 > fraction |
| `strength_in_area` | `side`, `ref`, `min_echelon` | ref 영역 안 그 진영 전투력 ≥ 제대 기준 (소대 1 · 중대 4 · 대대 15 · 연대 48 유닛) |
| `time_elapsed` | `value` | t ≥ value (일정에만 쓴다) |

`t`는 **D일 00:00부터의 시간**이다. D+1일 06:00 = 30.

## 새 COA를 생성할 때

- **입력**: `data/anon/<id>.json`의 `input`. 실명·날짜·작전명을 별칭으로 바꾼 것이다. id와 좌표는 원본과 같다.
- **few-shot 예시**: 다른 사례의 `anon` `{input → order}` 쌍. **평가할 사례 자신은 예시에서 뺀다**(leave-one-out).
- **출력 형식**: [`schema/order.schema.json`](schema/order.schema.json). 구조화 출력 스키마로 그대로 쓸 수 있다.
- **생성 모델에 주면 안 되는 것**: `meta`, `scenario`, `history`, `checks`. 숨은 적과 실제 결과가 들어 있다.
- **검사**: `tools/validate_order.py <case> <new_order>`. 오류가 있으면 시뮬레이션하지 않는다.
  - 오류: 구조, 정의되지 않은 id, 동사의 params 누락, 전투력 조건이 아닌 반응 조건, 첫 항목의 '이어서', 캔버스 밖 좌표
  - 경고: basis 누락, '즉시' 문장의 숨은 조건, 금지 표현, 숨은 적 참조

## 알아 둘 한계

- **좌표는 대부분 추정이다.** 지형지물 741개 중 703개가 `estimated: true`다. 상대 위치는 맞지만 수백 m 정밀도는 기대하지 않는다.
- **유닛 환산표와 계수는 보정 전 초안이다.** 모범 답안을 돌려 실제 결과에 맞추는 것이 첫 작업이다([02 §7](docs/02_simulator_contract.md#7-종료와-평가)).
- **20건은 `outcome_free = false`다.** 시나리오의 일부 '계획' 항목에 실제 결과가 섞였을 수 있다. 보정 기준선에서는 우선 빼는 것을 권한다([CASES.md](data/CASES.md)).
- **의미 검사가 지적한 49개 항목(29건)은 사람이 확인하지 않았다.** `meta.semantic_audit.flagged`에 있다.
- **`history`의 손실률은 약 40건에만 있다.** 나머지는 문장(`losses`)뿐이다.
- 데이터에 없는 구현 판단(동사 → SC2 행동, '이어서' 완료, 장악 기준 등)은 [05. 열린 질문](docs/05_open_questions.md)에 모았다.

## 문의와 수정 요청

데이터 표현이 부족하거나 틀린 곳을 찾으면 사례 id와 JSON 경로(예: `kb2_023 scenario.enemy_plan.groups[6].items[2]`)를 적어 데이터 쪽에 알려 준다. 스키마를 바꿔야 하면 0.7로 올려 반영하고 [CHANGELOG](CHANGELOG.md)에 남긴다.
