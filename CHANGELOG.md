# CHANGELOG

## 레포 구조 개편 — 2026-10-19

데이터 내용과 스키마(`reduced-opord/0.6`)는 그대로이고, 파일 배치와 도구만 바꿨다.

- **사례 하나 = 폴더 하나**(`cases/<id>/`). 블록마다 파일이 하나씩이다: `situation.json`, `coa.json`, `scenario.json`, `history.json`, `source.json`, `real_names/`. 같은 `input`이 세 파일에 중복되던 것이 없어졌다.
- 사례 폴더마다 `README.md`(요약·약도·명령서)를 두었다.
- 도구를 패키지 하나로 모았다: `python -m pseudo_coa list | show | validate | sim-input | eval-target | prompt | generate`.
- 시뮬레이터 입력(`sim-input`)의 `input`은 익명판이다(전에는 실명판). id와 좌표가 같아 시뮬레이션에는 차이가 없다.
- 스키마를 블록별로 나눴다. 옛 `order.schema.json`은 `coa.schema.json`, 옛 `reduced-opord-0.6.schema.json`은 `case.schema.json`이다.
- 문서를 독자별로 나눴다(`docs/tutorial`, `docs/simulation`, `docs/generation`, `docs/reference`). 실험은 `experiments/<날짜>_<이름>/`에 둔다.
- `cases.csv`에 `calibration_ok`(보정 기준선에 써도 되는가)와 `human_reviewed` 열을 두었다.

옛 경로와 새 경로의 대응은 다음과 같다.

| 옛 경로 | 새 경로 |
|---|---|
| `data/situations/<id>.json` | `cases/<id>/situation.json` (+ `mission_type`) |
| `data/pseudo_gt/<id>.json` | `cases/<id>/situation.json` + `cases/<id>/coa.json` |
| `data/sim_cases/<id>.json` | `cases/<id>/`의 파일들. 실명판 input·order는 `real_names/`. 합친 꼴은 `pseudo_coa.load_case(id).full()` |
| `data/readable/<id>.order.md`, `.map.svg` | `cases/<id>/README.md`, `cases/<id>/map.svg` |
| `data/case_list.jsonl`, `data/README.md` | `cases/cases.csv`, `cases/README.md` |
| `tools/validate_order.py <case> <order>` | `python -m pseudo_coa validate <id> <order>` |
| `tools/case_io.py sim/eval/prompt` | `python -m pseudo_coa sim-input / eval-target`, `cases/<id>/situation.json` |
| `generation/generate_coa.py` | `python -m pseudo_coa generate / prompt`, `pseudo_coa/generate/` |
| `experiment/` | `experiments/2026-10-19_fewshot/` |
| `tutorial/` | `docs/tutorial/` |

## 스키마 0.6 — 2026-10-16 (현재)
반응 조건을 **전투력**으로 좁혔다.
- 반응 조건(아군 '명에 의해', 예비 투입, 적 '조건', 상급 '조건')은 `losses_exceed`와 `strength_in_area`만 쓴다.
- `strength_in_area`를 더했다(`side`, `ref`, `min_echelon`, 선택 `group`). 적이 야간 침투나 우회로 진지 안에 들어왔는데 지키는 부대의 손실은 작은 경우에 예비가 움직이게 하려는 것이다.
- 순서는 조건이 아니라 `timing: "이어서"`로 쓴다. 초월 뒤 탈취, 전초 탈취 뒤 주봉 공격 같은 것이다.
- 계획 시각(H시, 적의 계획된 공격 개시)은 조건이 아니라 일정이다. `time_elapsed`로 쓴다.
- 위치만의 진입, 지점 도달, 돈좌, 접촉 단절, 기상·명암은 조건으로 쓰지 않는다. 기상·명암의 효과는 `scenario.exogenous`로 준다.
- 검사를 더했다: `on_order_not_state`, `enemy_rule_not_state`, `higher_rule_not_state`, `reserve_commit_not_power`, `power_cond_incomplete`, `sequence_invalid`, `plan_combat_cue`.

## 0.5 — 2026-10-16
**결과는 시뮬레이터가 낸다**는 원칙을 세웠다.
- `sim` 블록을 `scenario`(시뮬레이터 입력)와 `history`(평가 전용)로 나눴다.
- 구간을 결과("주봉을 잃을 때까지")가 아니라 `start_t`와 `horizon_h`로 정한다.
- 적 계획을 `timing`(계획 / 조건)으로 나누고 `repeat`, `basis`를 더했다.
- `scenario.hidden_enemy`(연대가 몰랐던 적), `scenario.exogenous`(외생 사건), `input.higher_context.higher_rules`(상급·인접 부대의 조건부 행동)를 더했다.
- 결과가 섞였는지 보는 규칙 검사(`result_in_scenario`, `plan_reactive` 등)와 의미 검사(`meta.semantic_audit`)를 더했다.

## 0.4 — 2026-10-15
명령서 구조와 좌표를 정했다.
- 단계화하지 않은 초기 배치 명령 하나로 바꿨다. 구간 중 결심은 '명에 의해' 과업으로 쓴다.
- 교범 전술과업 32개로 과업 동사를 제한했다.
- order 구조를 명령서 번호(전투편성, 1항 가~다, 2항, 3항 가~라)에 맞췄다.
- 200×200 좌표 캔버스, 배치 좌표·정면 폭·다각형·중대 위치, 경유점 경로, 축척을 넣었다.
- 부대 규모를 정형화했다(`echelon`, `type`, `modifier`, `strength_pct`). 유닛 환산은 `sim_unit_table.json`으로 분리했다.
