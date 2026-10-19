# JSON 필드 사전 (`reduced-opord/0.6`)

사례 하나는 전투 하나의 한 구간이고, `cases/<id>/` 폴더 하나입니다. 연대급 관점에서 명령 시점의 상황(`input`), 그 연대가 내린 초기 배치 명령(`order`), 시뮬레이터가 돌릴 적 계획과 환경(`scenario`), 실제 경과(`history`)를 담습니다. 블록마다 파일이 하나씩입니다.

| 파일 | 최상위 키 | 블록 | 스키마 |
|---|---|---|---|
| `situation.json` | `id`, `schema`, `mission_type`, `input` | [input](#input) (익명화) | `schema/situation.schema.json` |
| `coa.json` | `id`, `schema`, `order` | [order](#order) (익명화) | `schema/coa.schema.json` |
| `scenario.json` | `id`, `schema`, `scenario` | [scenario](#scenario) | `schema/scenario.schema.json` |
| `history.json` | `id`, `schema`, `history` | [history](#history) | `schema/history.schema.json` |
| `source.json` | `id`, `schema`, `meta`, `checks` | [meta](#meta), [checks](#checks) | `schema/source.schema.json` |
| `real_names/situation.json`, `real_names/coa.json` | 위와 같음 | 실명판 input, order | 위와 같음 |

`pseudo_coa.load_case(id).full()`은 이 파일들을 합쳐 아래 [최상위](#최상위) 꼴의 dict 하나로 돌려줍니다(실명판).

기계가 읽는 정의는 [`schema/`](../../schema)의 블록별 스키마와 합친 꼴의 [`schema/case.schema.json`](../../schema/case.schema.json)입니다. 이 문서는 그 정의를 사람이 읽도록 풀어 쓴 것입니다. 표의 **필수** 열은 스키마의 required입니다. **시뮬** 열은 시뮬레이터가 읽어야 하는 필드(●), 참고만 하는 필드(○), 읽지 않는 필드(빈칸)입니다.

- [공통 규칙](#공통-규칙)
- [최상위](#최상위)
- [meta](#meta)
- [input](#input)
- [order](#order)
- [scenario](#scenario)
- [history](#history)
- [checks](#checks)
- [사건 객체](#사건-객체-event)

---

## 공통 규칙

| 항목 | 규칙 |
|---|---|
| 좌표 `xy` | `[x, y]`. 캔버스 200×200, 원점 왼쪽 아래, 북쪽 +y, 동쪽 +x. 1단위 = `meta.geo.scale_m_per_unit` m (50건 모두 100m) |
| 선·경로 | `[[x,y], …]` 경유점 목록 (도로, 축선 `axis_xy`, 전투지경선) |
| 다각형 `polygon` | `[[x,y], …]` 꼭짓점 목록, 닫는 점은 반복하지 않음 |
| 시각 `t` | D일 00:00부터의 경과 시간(시간 단위, 실수). D+1일 06:00 = 30, D-1일 22:00 = -2 |
| 시각 문장 `when`, `text` | 사람이 읽는 표기 ("D일 19:15", "D+1일 새벽"). 시뮬레이터는 `t`·`value`만 읽습니다 |
| id | 사례 안에서만 유일합니다. 지형 `H395`, 통제수단 `CM_*`, 가용 부대 `F*`, 편성 그룹 `G*`, 적 `E*`, 숨은 적 `HE*`, 인접 부대 `ADJ*` 같은 관례가 있지만 접두어에 의미를 두지 말고 정의된 목록으로 찾습니다 |
| 지형 참조 `*_ref`, `ref`, `objective`, `area`, `line(s)`, `route` … | `input.terrain.features/routes/impassable`, `input.area_of_operations.boundaries`, `order.execution.coordinating.control_measures`의 id |
| 부대 참조 `group`, `*_group`, `main_effort` | 편성 그룹 `G*`, 적·숨은 적 id, 인접 부대 id |
| `estimated` | 참이면 서술로 추정한 좌표, 거짓이면 아틀라스 상황도에서 잰 좌표(오차 약 ±200m) |
| `alias`, `other_names` | 익명화용 이름. 시뮬레이터와 무관 |
| 문장 필드 (`text`, `note`, `why`, `purpose`, `basis`, `evidence`) | 사람이 읽는 설명. 시뮬레이터는 읽지 않습니다 |

## 최상위

| 키 | 필수 | 시뮬 | 내용 |
|---|---|---|---|
| `schema` | ● | | 항상 `"reduced-opord/0.6"` |
| `id` | ● | | 사례 id (`kb1_062`, `kb2_023` …). 폴더 이름과 같습니다 |
| `meta` | ● | ○ | 출처, 구간, 결과 라벨, 좌표계 |
| `input` | ● | ● | 명령 시점의 상황 |
| `order` | ● | ● | 연대의 초기 배치 명령 (새 COA가 대신하는 블록) |
| `scenario` | ● | ● | 적 계획, 숨은 적, 외생 사건, 시뮬레이션 시간 |
| `history` | ● | | 실제 경과. **시뮬레이터에 주지 않습니다** |
| `checks` | | | 생성 뒤 붙인 품질 검사 결과 |
| `aliases_extra` | | | 15건에만 있음. 문장 속 추가 익명화 치환표 |

---

## meta

시뮬레이터는 `geo.scale_m_per_unit`만 읽습니다. 나머지는 사례를 고르거나 보고서를 쓸 때 씁니다.

| 키 | 시뮬 | 내용 |
|---|---|---|
| `title`, `dates`, `branch`, `source`, `pdf_page` | | 전투 이름, 기간, 출처(국방부 군사편찬연구소 『6·25전쟁 주요전투』) |
| `bucket` | | 전투 범주: 고지 방어·탈환 / 능선 공격 / 하천선 방어·방어 후 역습 / 지연·철수·사주방어 |
| `mission_type` | | 지역방어 / 공격 / 역습 / 지연 |
| `segment` | | `start_date`, `end_date`, `d_day`(달력의 D일), `order_time`(명령 시점), `text`, `why` |
| `perspective_rationale` | | 관점 연대를 고른 이유 |
| `outcome` | | `label`(success / partial / failure), `evidence`. 구간의 실제 결과 요약 |
| `geo` | ● | `scale_m_per_unit`, `origin`(무엇이 어느 좌표인가), `source`(text / atlas+text), `atlas_pages` |
| `triage`, `triage_counterfactuals[]` | | 사례 선별 점수, 이 사례에서 갈림길이 된 결심과 대안 |
| `semantic_audit` | | 시나리오에 결과가 섞였는지 본 의미 검사(Sonnet) 결과. `flagged[]{id, verdict, reason, fix}` |
| `gen`, `*_normalized`, `spec_used`, `sim_unit_table`, `seed_id`, `segment_suggestion`, `manual_fixes` | | 생성 기록 |

---

## input

명령 시점에 연대가 알았거나 알 수 있었던 것입니다. 생성 모델(에이전트)에게는 이 블록의 익명화본(`cases/<id>/situation.json`의 `input`)을 줍니다. 실명판은 `cases/<id>/real_names/situation.json`에 있습니다.

### `input.perspective`
| 키 | 필수 | 내용 |
|---|---|---|
| `unit`, `alias`, `echelon` | ● | 관점 부대. `echelon`은 연대 / 해병연대 |
| `other_names` | | |

### `input.higher_context`
| 키 | 필수 | 시뮬 | 내용 |
|---|---|---|---|
| `higher_unit`, `higher_alias`, `higher_mission`, `higher_intent`, `assigned_task` | ● | | 상급 사단의 임무·의도, 연대가 받은 과업 |
| `adjacent_units[]` | ● | ● | 인접 부대. `id`, `unit`, `side`("좌측(서쪽)", "후방(사단 예비)" 같은 자유 문장), `mission`, `echelon`, `type`, `xy`. 위치는 `xy`로 읽습니다 |
| `higher_rules[]` | ● | ● | 상급·인접 부대의 행동 규칙 (아래) |

`higher_rules[]` — 연대가 명령 시점에 알고 있던 상급·인접 부대의 행동. 예: "적 대대 이상이 주봉에 있으면 사단 예비가 역습한다."

| 키 | 필수 | 내용 |
|---|---|---|
| `unit` | ● | 행동하는 부대. 인접 부대 id(`ADJ*`), 편성 그룹 id, 또는 지도 밖 화력이면 부대 이름 |
| `timing` | | `계획`(trigger가 time_elapsed인 일정) / `조건`(trigger가 전투력 조건) |
| `trigger` | ● | [사건 객체](#사건-객체-event) |
| `action` | ● | `mode`(적 행동과 같은 어휘), `objective_ref`, `axis_xy` |
| `delay_h` | | 조건 충족 뒤 시작까지 지연 시간 (1건에만 있음) |
| `text` | ● | 설명 |

### `input.area_of_operations`
| 키 | 내용 |
|---|---|
| `text` | 작전지역 설명 |
| `boundaries[]` | 상급이 준 연대 경계. `id`, `name`, `between`(양쪽 부대 이름), `xy`(선), `estimated` |

### `input.available_forces[]` — 연대가 쓸 수 있는 부대
| 키 | 필수 | 시뮬 | 내용 |
|---|---|---|---|
| `id` | ● | ● | `F*`. 편성 그룹의 `composition[].force`가 이 id를 가리킵니다 |
| `unit`, `alias` | ● | | 이름 |
| `echelon` | ● | ● | 분대 / 소대 / 중대 / 포대 / 대대 / 연대 / 여단 / 사단 |
| `type` | ● | ● | infantry / armor / mech_infantry / artillery / mortar / antitank / aviation / engineer / recon / marine / other |
| `modifier` | ● | ● | `""` / `"+"` / `"-"` (증강·감소) |
| `strength_pct` | ● | ● | 명령 시점 충원율(%). 모르면 100 |
| `personnel`, `equipment` | | ○ | 알 때만. 예: "105mm 6문", "전차 17대" |
| `relationship` | ● | ○ | 건제 / 배속 / 작전통제 / 직접지원 / 일반지원 |
| `location` | ● | ○ | 명령 전 위치 `{note, xy?, ref?}`. 이미 진지에 있는 부대는 note만 있고 실제 배치는 `order…deploy`에 있습니다 |

규모를 유닛 수로 바꾸는 규칙은 [`sim_unit_table.json`](../../sim_unit_table.json)과 [시뮬레이션 방법 §3](../simulation/how_to_simulate.md#3-부대를-유닛으로-바꾸기)을 봅니다.

### `input.terrain`
| 키 | 필수 | 내용 |
|---|---|---|
| `canvas` | ● | `[200, 200]` |
| `scale_m_per_unit` | ● | meta와 같은 값 |
| `area_text` | ● | 지형 설명 |
| `features[]` | ● | 지형지물 (아래) |
| `routes[]` | ● | 도로·통로. `id`, `kind`(road / trail / ridge / valley / rail), `xy`(경유점), `estimated` |
| `impassable[]` | ● | 통과 불가 지역. `id`, `polygon`, `active`(항상 / 구간 중 발생), `gap_at`(통과 가능한 틈 xy, 예: 도하점) |

`features[]`
| 키 | 필수 | 내용 |
|---|---|---|
| `id`, `name`, `alias` | ● | |
| `kind` | ● | hill / ridge / river / lake / crossing / bridge / town / valley / pass / area / other |
| `xy` | ● | 대표점(고지면 정상) |
| `line`, `polygon` | | 선형(능선·하천)이나 지역이면 |
| `elevation_m` | ● | 표고. 모르면 0 |
| `preparation` | | 그 지형의 진지 준비: none / hasty / deliberate / fortified |
| `estimated`, `evidence` | ● | 좌표 출처 |

`active: "구간 중 발생"`인 통과 불가 지역은 처음에는 꺼져 있습니다. 켜지는 시각은 `scenario.exogenous`의 같은 `ref` 사건(예: `flood`)이 정합니다.

### `input.enemy_forces[]` — 연대가 알고 있던 적
| 키 | 필수 | 내용 |
|---|---|---|
| `id` | ● | `E*`. enemy_plan의 `group`이 이 id입니다 |
| `echelon`, `type`, `modifier`, `strength_pct` | ● | 가용 부대와 같은 규모 표기 |
| `nation` | ● | 북한 / 중국 |
| `identified`, `known_at_start` | ● | 식별 여부, 무엇을 어떻게 알았나 |
| `posture` | ● | 방어 / 공격준비 / 예비 / 이동 / 미상 |
| `preparation` | | none / hasty / deliberate / fortified |
| `position` | ● | `{xy, note, ref?, polygon?, frontage_m?}` 처음 위치 |

### `input.conditions`
| 키 | 내용 |
|---|---|
| `start_time` | 시작 시각 문장 (`scenario.start`와 같습니다) |
| `light` | day / night / dawn / dusk |
| `notes` | 설명 |

---

## order

연대의 초기 배치 명령 하나입니다. 단계(1단계·2단계)로 나누지 않습니다. 구간 중의 결심은 "명에 의해" 과업과 그 조건으로 미리 적습니다. **새로 생성한 COA는 이 블록을 통째로 대신합니다.**

명령서 항목과 경로:

| 명령서 | 경로 | 시뮬 |
|---|---|---|
| 전투편성 | `task_organization` | ● |
| 1. 상황 가. 지형 / 나. 적 / 다. 가정 | `situation.terrain` / `situation.enemy` / `situation.assumptions` | ○ |
| 2. 임무 | `mission` | ○ |
| 3. 실시 가. 최종상태 | `execution.end_state` | ○ |
| 나. 작전개념 (1) 기동 (2) 화력 | `execution.concept` | ● (주력, 예비, 화력 우선) |
| 다. 예하부대 과업 | `execution.tasks` | ● |
| 라. 협조지시 (1) 시간계획 (2) 통제수단 | `execution.coordinating` | ● |

4항 지속지원과 5항 지휘통신은 없습니다.

### `order.task_organization`
| 키 | 필수 | 내용 |
|---|---|---|
| `text` | ● | 한 줄 표기. 예: "제1대대(+제11중대), 제2대대, 제3대대(-) / 지원: 사단 포병, 제53전차중대" |
| `groups[]` | ● (2개 이상) | 과업 단위 |
| `groups[].id` | ● | `G1`, `G2` … |
| `groups[].label` | ● | 명령서 표기 |
| `groups[].kind` | ● | 기동 / 예비 / 화력지원 / 경계 |
| `groups[].composition[]` | ● | `{force: "F1"}` 또는 일부만이면 `{force: "F3", part: "제11중대"}`, 떼어 낼 때 `{force: "F3", part: "-제11중대"}` |

직접지원 포병·항공처럼 group으로 만들지 않은 지원은 `text`의 "지원:" 뒤에만 있습니다.

### `order.situation`
시뮬레이터는 읽지 않습니다. 생성 모델이 판단을 드러내는 부분이고, 평가할 때 읽습니다.

| 키 | 내용 |
|---|---|
| `terrain.text`, `key_terrain[]{ref, why}`, `avenues[]{name, user, refs, xy}` | 핵심 지형과 접근로 |
| `enemy.text` | 적 최유력 방책 문장 |
| `enemy.most_likely_coa.steps[]` | `group`, `mode`, `from_ref`(선택), `objective_ref`, `axis_xy`, `when`, `t` |
| `enemy.most_likely_coa.risk_point` | 아군에게 가장 위험한 순간. 예비 투입 조건의 근거 |
| `enemy.unknowns[]` | 모르는 것 |
| `assumptions[]{text, why}` | 가정 1~4개 |

### `order.mission`
| 키 | 내용 |
|---|---|
| `text` | 임무 한 문장 |
| `task_verb` | 과업 동사 (아래 목록) |
| `objective_ref` | 목표 지형 |
| `when` | 사건 객체 (항상 time_elapsed) |
| `purpose` | 목적 |

### `order.execution.end_state`
`text`, `friendly`, `enemy`, `terrain` 문장. 평가 때 읽습니다.

### `order.execution.concept`
| 키 | 시뮬 | 내용 |
|---|---|---|
| `text`, `maneuver`, `fires` | | 문장 |
| `main_effort` | ○ | 주력 group id |
| `reserve.group` | ● | 예비 group id. 예비가 없으면 `"없음"` |
| `reserve.position_ref`, `reserve.xy` | ● | 예비 위치 |
| `reserve.commit` | ● | 예비 투입 조건. 전투력 조건 [사건 객체](#사건-객체-event) |
| `reserve.priorities[]` | | 투입 우선순위 문장 |
| `fire_support.priority_groups[]` | ● | 화력 우선 지원 group |
| `fire_support.zone_refs[]` | ● | 화력 집중 지역 (주로 교전지역 EA) |
| `fire_support.restrictions` | ○ | 사격 제한 문장 |

예비 group의 `tasks[]`에도 같은 조건의 "명에 의해" 역습 과업이 들어 있습니다. 시뮬레이터는 과업 쪽을 실행하면 됩니다. `reserve.commit`은 같은 조건을 개념 수준에서 다시 적은 것입니다.

### `order.execution.tasks[]` — 예하부대 과업 (시뮬레이터의 핵심 입력)
| 키 | 필수 | 내용 |
|---|---|---|
| `group` | ● | 편성 group id. 기동·예비·경계 group은 모두 과업이 있습니다 |
| `purpose` | ● | 문장 |
| `deploy` | ● | 명령 시점의 배치 (아래) |
| `items[]` | ● (1~4개) | 과업 목록. 순서가 실행 순서입니다 |

`deploy`
| 키 | 필수 | 내용 |
|---|---|---|
| `kind` | ● | 진지 / 전초 / 예비진지 / 화력지원진지 / 공격대기지점 / 집결지 / 지역 / 이동 중 |
| `xy` | ● | 배치 중심 |
| `ref` | | 그 배치가 있는 지형·통제수단 |
| `frontage_m`, `depth_m` | | 정면 폭과 종심(m) |
| `polygon` | | 배치 지역 |
| `preparation` | | none / hasty / deliberate / fortified |
| `elements[]` | | 예하 중대 위치 `{label, xy, ref?}` |
| `note` | ● | 설명 |

`items[]`
| 키 | 필수 | 내용 |
|---|---|---|
| `timing` | ● | **즉시** (시작과 함께) / **이어서** (같은 목록의 바로 앞 항목이 끝나면) / **명에 의해** (`trigger`가 참이 되면) |
| `verb` | ● | 과업 동사 (아래) |
| `params` | ● | 동사에 필요한 대상 (아래) |
| `trigger` | 명에 의해일 때 ● | 전투력 조건 [사건 객체](#사건-객체-event). 즉시·이어서에는 없습니다 |
| `basis` | 명에 의해일 때 ● | 그 대비 계획의 근거 (예: "risk_point: 적이 주봉에 돌입") |
| `text` | ● | 명령 문장 |

과업 동사 32개와 필요한 `params`:

| 분류 | 동사 → 필요한 params |
|---|---|
| 지형 | 탈취·확보·점령·고수·소탕 → `objective` / 정찰 → `area` |
| 적 | 격멸·격퇴·와해·고착·봉쇄·무력화·우회·견제 → `target_group` 또는 `target_ref` / 차단·저지 → `line` 또는 `area` / 돌파 → `axis_xy`, `objective` |
| 기동 | 공격 → `objective` / 역습 → `objective`, `route` / 방어 → `area` / 지연 → `lines`, `disengage` / 추격 → `limit_line` / 철수·이탈 → `destination` |
| 아군 | 엄호 → `covered_group` / 경계·차장 → `area` / 후속지원·후속인수 → `followed_group` / 초월 → `passed_group`, `passage_point` |
| 화력 | 화력지원 → `supported_group`, `target_ref` / 화력공격 → `target_ref` |

`params.disengage`(지연)는 이탈 조건을 적은 사건 객체입니다(`losses_exceed`). 실제로 쓰인 동사의 빈도는 [열거값 사전](../reference/vocabulary.md)을 봅니다.

### `order.execution.coordinating`
| 키 | 필수 | 내용 |
|---|---|---|
| `time_plan[]` | ● (1개 이상) | `{text, event}`. 진지 점령 완료, H시, 예비 준비 완료 시각. event는 대부분 time_elapsed |
| `control_measures[]` | ● (2개 이상) | 통제수단 (아래) |

`control_measures[]`
| 키 | 필수 | 내용 |
|---|---|---|
| `id`, `name` | ● | 과업·조건의 `ref`가 이 id를 가리킵니다 |
| `kind` | ● | boundary / contact_point / phase_line / line_of_departure / passage_point / assembly_area / attack_position / battle_position / objective / engagement_area / route / axis / checkpoint / outpost / target / limit_of_advance / other |
| `xy` | ● | 점이면 1개, 선이면 2개 이상, 지역이면 3개 이상(다각형) |
| `terrain_refs[]` | | 걸쳐 있는 지형 id |
| `between[]` | | 경계·접촉점의 양쪽 group |
| `preparation` | | 진지 준비 |
| `estimated` | ● | |

---

## scenario

시뮬레이터만 읽습니다. 생성 모델에게 주지 않습니다. 결과(피탈, 격퇴, 철수 같은 것)는 넣지 않는다는 원칙으로 만들었습니다.

| 키 | 필수 | 내용 |
|---|---|---|
| `start`, `start_t` | ● | 시작 시각 문장과 t |
| `horizon_h` | ● | 시뮬레이션 길이(시간). 끝 시각은 `start_t + horizon_h` |
| `stop_conditions[]` | ● | 조기 종료 조건. 모두 `losses_exceed`(and로 묶음 포함). 목록 중 하나라도 참이면 끝냅니다. `group` 없이 `side`만 있으면(5건) 그 진영 전체의 누적 손실입니다 |
| `enemy_plan.intent` | ● | 적 상급부대 의도 문장 |
| `enemy_plan.groups[]` | ● | 적 부대별 행동 목록 `{group, items[]}` |
| `hidden_enemy[]` | ● | 연대가 몰랐던 적. `enemy_forces`와 같은 규모 표기 + `position{xy, note, ref?}` |
| `exogenous[]` | ● | 외생 사건 |

`enemy_plan.groups[].items[]`
| 키 | 필수 | 내용 |
|---|---|---|
| `timing` | ● | **계획** (`start` 시각에 시작) / **이어서** (바로 앞 항목이 끝나면) / **조건** (`trigger`가 참이 되면) |
| `mode` | ● | attack / counterattack / infiltrate / fix / hold / bombard / reinforce / withdraw / pursue (스키마에는 demolish도 있으나 미사용) |
| `objective_ref` | | 목표 지형 |
| `target_ref` | | 드묾(kb1_070의 3건). 지형이 아니라 **아군 group id**(`G1` 등)를 가리킵니다. 그 부대를 고착·공격한다는 뜻 |
| `from_ref` | | 출발 지형 (kb2_008의 3건) |
| `axis_xy` | | 축선 경유점 |
| `start` | 계획일 때 ● | time_elapsed 사건 |
| `trigger` | 조건일 때 ● | 전투력 조건 사건 |
| `repeat` | | 같은 행동의 반복 `{max, interval_h}` |
| `basis` | ● | 근거 (추정이면 "추정") |
| `text` | ● | 설명 |

`exogenous[]`
| 키 | 내용 |
|---|---|
| `t`, `when` | 시작 시각 |
| `kind` | night / dawn / air_window / weather / fog / flood / other |
| `duration_h` | 지속 시간 |
| `ref` | 영향을 받는 지형 (예: flood → `impassable`의 id, fog → 고지 id) |
| `note` | 설명 |

---

## history

**평가 전용입니다. 시뮬레이터에 주지 않습니다.** 두 가지에 씁니다. (1) 보정: pseudo-GT `order`로 돌린 결과가 이것과 비슷해지도록 계수를 맞춥니다. (2) 비교: 새 COA의 결과를 실제 결과·pseudo-GT 결과와 견줍니다.

| 키 | 내용 |
|---|---|
| `enemy_actual[]` | `{group, actions[{when, t, mode, from_ref?, target_ref?, axis_xy, note}]}` 적의 실제 행동 |
| `friendly_actual[]` | `{group, actions[{when, t, verb, ref?, text}]}` 아군 실제 행동 (연대 밖 상급 예비 포함) |
| `reinforcements_actual[]` | `{id, unit, entry_when, entry_t, from_ref?, note}` 실제 증원 투입 |
| `environment_actual[]` | `{when, t, kind, ref?, note}` 실제 환경 (kind: night / air / weather / fog / flood / other) |
| `historical_result` | `friendly`, `enemy`, `terrain_held[]`, `end_state_achieved`(yes / partial / no), `losses`(문장), `duration_h`, `friendly_loss_pct`·`enemy_loss_pct`(알 때만, 약 40건) |
| `outcome_metrics` | **비교 기준.** 시뮬레이션 끝 시각의 실제 상태: `status_at_horizon`(문장), `terrain_held_at_horizon[]`(아군이 쥔 지형 id), `key_times[]{t, text, ref}`, 손실률(알 때만) |

---

## checks

생성기가 붙인 규칙 검사 결과입니다. 키마다 위반 목록이고 비어 있으면 통과입니다. 요약 불리언은 넷입니다.

| 키 | 뜻 |
|---|---|
| `sim_projectable` | 참조·동사·조건·배치·좌표가 시뮬레이터에 넣을 수 있는 구조인가 (50건 모두 참) |
| `outcome_free` | 시나리오에 결과 표현이 없는가 (30건 참, 20건 거짓) |
| `doctrine_clean` | 교리 어휘를 지켰는가 |
| `anonymization_clean` | 익명화 뒤 실명이 남지 않았는가 |

사례별 표시는 [`cases/README.md`](../../cases/README.md)에 정리했습니다.

---

## 사건 객체 (event)

조건과 시각은 모두 같은 꼴의 사건 객체로 씁니다. `trigger`, `start`, `commit`, `when`, `event`, `disengage`, `stop_conditions[]`가 이 꼴입니다.

```jsonc
{ "type": "strength_in_area", "side": "enemy", "ref": "H395", "min_echelon": "중대",
  "text": "적 중대 이상이 395고지 주봉 지역 안에 있음" }
```

| type | 필드 | 뜻 | 쓰는 곳 |
|---|---|---|---|
| `time_elapsed` | `value` (t) | 그 시각이 됨. **조건이 아니라 일정입니다** | 적 '계획' start, 상급 '계획' 규칙, 시간계획, 임무 when |
| `losses_exceed` | `group`, `fraction` (0~1] | 그 부대의 누적 손실 비율이 fraction을 넘음 | 반응 조건, 종료 조건, 지연 이탈 |
| `strength_in_area` | `side`(friendly / enemy), `ref`, `min_echelon`(소대 / 중대 / 대대 / 연대), `group`(선택) | ref 지역 안에 side의 전투력이 그 제대 규모 이상 있음 | 반응 조건 |

- `text`는 모든 사건에 있습니다. 사람이 읽는 설명입니다.
- 복합 조건: `"and": [사건, …]`. 바깥 사건과 and 안의 사건이 모두 참이어야 참입니다. 바깥 사건에 `group`·`ref`가 없으면 바깥은 묶음으로만 쓰인 것이고 and 안의 사건만 봅니다.
- **반응 조건**(아군 '명에 의해', 예비 투입, 적 '조건', 상급 '조건')은 `losses_exceed`와 `strength_in_area`만 씁니다. 위치 진입, 지점 도달, 돈좌, 접촉 단절, 기상, 상급 승인은 조건으로 쓰지 않습니다. 이전 버전(0.4·0.5)의 `enemy_in_area`, `group_reaches_point`, `group_halted` 같은 type은 0.6 데이터에 없습니다.
- 판정 방법은 [시뮬레이션 방법 §4](../simulation/how_to_simulate.md#4-사건-판정)를 봅니다.
