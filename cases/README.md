# cases — 사례 50건

사례 하나는 폴더 하나입니다(예: [`kb2_023/`](kb2_023/)). 폴더 안의 파일은 블록마다 하나씩이고, **파일 이름만 보고 누구에게 줘도 되는지 알 수 있게** 나눴습니다.

| 파일 | 내용 | 생성 모델 | 시뮬레이터 |
|---|---|---|---|
| `situation.json` | ① 상황(`input`): 명령 시점에 연대가 알던 것. 상급 임무, 작전지역, 가용 부대, 지형 좌표, 적. **익명화** | ○ 입력 | ○ |
| `coa.json` | ② pseudo-GT COA(`order`): 그 연대가 실제로 내린 초기 배치 명령. **익명화** | ○ 예시로만 | ○ (새 COA로 바꿔 끼움) |
| `scenario.json` | ③ 시나리오(`scenario`): 적의 실제 계획과 반응 규칙, 연대가 몰랐던 적, 야간·안개 같은 환경, 시작·끝 시각 | **✗** | ○ |
| `history.json` | ④ 실제 경과(`history`): 실제로 일어난 일과 끝 시각의 상태 | **✗** | **✗** 평가에만 |
| `source.json` | 출처, 구간, 결과 라벨, 축척(`meta`)과 자동 검사 결과(`checks`) | ✗ | 축척만 |
| `real_names/` | ①②의 실명판. 사람이 원문과 대조할 때 씁니다 | ✗ | 필요 없음 (id·좌표가 같습니다) |
| `README.md`, `map.svg` | 사람이 읽는 사례 요약·명령서(실명)와 좌표로 그린 약도. GitHub에서 폴더를 열면 바로 보입니다 | | |

- **익명화**: 지명·부대명·날짜를 별칭으로 바꿨습니다(`395고지` → `고지 A`, `제30연대` → `아군 연대`). 생성 모델이 전쟁사를 떠올려 답을 베끼지 못하게 하려는 것입니다. id와 좌표는 실명판과 같습니다.
- **시뮬레이터 입력**은 `python -m pseudo_coa sim-input <id> [--coa 새COA.json]`이 ①(또는 새 COA) + ② + ③ + 축척을 합쳐 만듭니다. ④는 넣지 않습니다.
- 블록별 필드 정의는 [JSON 필드 사전](../docs/reference/json_fields.md)에 있습니다.

## cases.csv

[`cases.csv`](cases.csv)는 사례당 한 줄 요약입니다(GitHub에서 표로 보입니다). `python -m pseudo_coa list`로도 볼 수 있습니다.

| 열 | 뜻 |
|---|---|
| `id` | 사례 id = 폴더 이름. `kb1_*`은 『6·25전쟁 주요전투』 1권, `kb2_*`은 2권 |
| `title`, `regiment` | 전투명, 관점 연대(실명) |
| `mission_type` | 지역방어 · 공격 · 역습 · 지연 |
| `category` | 전투 범주(고지 방어·탈환 등) |
| `outcome` | 그 구간의 실제 결과: success · partial · failure |
| `start_t`, `horizon_h` | 시뮬레이션 시작 시각(D일 00:00부터 시간), 시뮬레이션 길이(시간) |
| `coords` | 좌표 출처: `atlas+text`(상황도에서 잼) · `text`(서술에서 추정) |
| `forces`, `groups` | 가용 부대 수, pseudo-GT COA의 편성 그룹 수 |
| `calibration_ok` | 시뮬레이터 보정 기준선에 써도 되는가. 시나리오에 실제 결과가 섞였을 가능성을 규칙 검사가 표시한 20건은 `false` |
| `human_reviewed` | 사람이 pseudo-GT를 검토했는가: yes · partial · no |
| `audit_flags` | 자동 의미 검사가 시나리오에서 지적한 항목 수(사람 미확인). 자세한 내용은 `source.json`의 `meta.semantic_audit` |
| `source_volume` | 출처 책의 권 |

## 사례 목록과 품질 표시

각 사례의 `source.json`(`checks`, `meta.semantic_audit`)에서 뽑았습니다. 50건 모두 `sim_projectable`(시뮬레이터가 읽을 수 있는 구조)은 참입니다.

- **보정용**: `cases.csv`의 `calibration_ok`(= `checks.outcome_free`). 아니오면 시나리오에 실제 결과가 섞였을 가능성을 규칙 검사가 표시한 것입니다. 보정 기준선에서는 빼거나 해당 항목을 확인하고 씁니다.
- **의미 검사 지적**: claude-sonnet-5가 시나리오 항목을 실제 경과와 대조해 지적한 수(time_copied: 실제 시각을 계획으로 옮김, disguised_result: 결과를 계획처럼 씀, hidden_condition: 숨은 조건). 사람이 확인하지 않은 지적입니다.

| id | 전투 | 범주 | 임무 | 결과 | 시간(h) | 좌표 | 보정용 | 규칙 검사 표시 | 의미 검사 지적 |
|---|---|---|---|---|---|---|---|---|---|
| [kb1_039](kb1_039/) | 장림-운유산 전투 | 지연·철수·사주방어 | 지연 | partial | 24 | text | 예 | - | time_copied 2 |
| [kb1_043](kb1_043/) | 소양교 전투 | 하천선 방어·방어 후 역습 | 지역방어 | partial | 33 | text | 예 | - | disguised_result 1 |
| [kb1_047](kb1_047/) | 말고개 전투 | 고지 방어·탈환 | 지역방어 | success | 69 | text | 예 | - | time_copied 2, hidden_condition 1 |
| [kb1_054](kb1_054/) | 원미산-오류동 전투 | 고지 방어·탈환 | 지연 | success | 51 | text | 예 | - | time_copied 5, hidden_condition 1, disguised_result 1 |
| [kb1_062](kb1_062/) | 무극리 전투 | 하천선 방어·방어 후 역습 | 지역방어 | partial | 30 | atlas+text | **아니오** | plan_basis_outcome 1 | - |
| [kb1_070](kb1_070/) | 공주 전투 | 하천선 방어·방어 후 역습 | 지역방어 | failure | 54 | text | 예 | - | - |
| [kb1_071](kb1_071/) | 대평리 전투 | 하천선 방어·방어 후 역습 | 지역방어 | failure | 84.5 | text | **아니오** | plan_basis_outcome 1 | time_copied 1, disguised_result 1 |
| [kb1_080](kb1_080/) | 함창 전투 | 고지 방어·탈환 | 지역방어 | success | 35 | text | 예 | - | - |
| [kb1_083](kb1_083/) | 권빈리 전투 | 고지 방어·탈환 | 지역방어 | success | 66 | text | **아니오** | plan_combat_cue 2 | hidden_condition 2 |
| [kb1_085](kb1_085/) | 낙정리 전투 | 하천선 방어·방어 후 역습 | 지역방어 | success | 68 | text | 예 | - | - |
| [kb1_086](kb1_086/) | 의성 전투 | 고지 방어·탈환 | 지역방어 | failure | 44 | text | 예 | - | disguised_result 1 |
| [kb1_093](kb1_093/) | 수암산-유학산 전투 | 고지 방어·탈환 | 공격 | success | 67 | text | 예 | org_uncovered 1, task_text_ending 1 | hidden_condition 1 |
| [kb1_102](kb1_102/) | 마산 서북방 전투 | 하천선 방어·방어 후 역습 | 지역방어 | success | 150 | text | **아니오** | plan_basis_outcome 1 | hidden_condition 1 |
| [kb1_103](kb1_103/) | 수암산 전투 | 능선 공격 | 공격 | failure | 84 | text | **아니오** | org_uncovered 1, plan_basis_outcome 1 | hidden_condition 1 |
| [kb1_108](kb1_108/) | 영천 전투 | 지연·철수·사주방어 | 역습 | success | 34 | text | 예 | - | - |
| [kb1_136](kb1_136/) | 개천-비호산 전투 | 고지 방어·탈환 | 지역방어 | partial | 52 | text | 예 | - | - |
| [kb1_149](kb1_149/) | 원주 전투 | 고지 방어·탈환 | 공격 | success | 102 | text | **아니오** | plan_reactive 1 | - |
| [kb1_175](kb1_175/) | 매봉-한석산 전투 | 능선 공격 | 공격 | success | 84 | text | 예 | - | hidden_condition 1 |
| [kb1_185](kb1_185/) | 924고지 전투 | 능선 공격 | 공격 | success | 128 | text | 예 | - | disguised_result 1 |
| [kb1_186](kb1_186/) | 884고지 전투 | 고지 방어·탈환 | 공격 | success | 83 | text | **아니오** | plan_basis_outcome 1 | - |
| [kb1_187](kb1_187/) | 피의 능선 전투 | 능선 공격 | 공격 | success | 101 | text | 예 | org_uncovered 1 | - |
| [kb1_189](kb1_189/) | 단장의 능선 전투 | 능선 공격 | 공격 | success | 72 | atlas+text | **아니오** | task_text_ending 1, plan_reactive 1 | - |
| [kb1_190](kb1_190/) | 백석산 전투 | 능선 공격 | 공격 | success | 32 | text | 예 | - | - |
| [kb2_003](kb2_003/) | 제1차 월비산 전투 | 능선 공격 | 공격 | success | 96 | text | 예 | - | - |
| [kb2_005](kb2_005/) | 금성천-교암산 전투 | 능선 공격 | 공격 | success | 108 | text | **아니오** | plan_reactive 1 | hidden_condition 1 |
| [kb2_006](kb2_006/) | 제2차 가칠봉 부근 전투 | 능선 공격 | 공격 | partial | 85 | text | 예 | - | - |
| [kb2_008](kb2_008/) | 281고지 및 395고지 전투 | 고지 방어·탈환 | 지역방어 | partial | 61 | text | **아니오** | plan_basis_outcome 1 | disguised_result 2 |
| [kb2_009](kb2_009/) | 제2차 월비산 전투 | 고지 방어·탈환 | 지역방어 | failure | 150 | text | **아니오** | plan_basis_outcome 1 | hidden_condition 1 |
| [kb2_011](kb2_011/) | 임진강 부근 전투 | 고지 방어·탈환 | 역습 | partial | 52 | text | **아니오** | plan_reactive 1 | hidden_condition 1 |
| [kb2_013](kb2_013/) | 두매리 전투 | 고지 방어·탈환 | 공격 | failure | 35 | text | 예 | - | - |
| [kb2_017](kb2_017/) | A고지 및 B고지 전투 | 고지 방어·탈환 | 공격 | success | 20.5 | text | **아니오** | plan_reactive 1 | time_copied 1, hidden_condition 1 |
| [kb2_018](kb2_018/) | 수도고지 및 지형능선 전투 | 고지 방어·탈환 | 지역방어 | partial | 86 | text | 예 | - | time_copied 1 |
| [kb2_019](kb2_019/) | 351고지 전투 | 고지 방어·탈환 | 역습 | success | 76 | text | 예 | - | - |
| [kb2_020](kb2_020/) | 벙커고지(122고지) 부근 전투 | 고지 방어·탈환 | 지역방어 | success | 76 | text | **아니오** | plan_basis_outcome 1 | disguised_result 1, time_copied 1 |
| [kb2_021](kb2_021/) | 피의고지 및 독수리고지 전투 | 고지 방어·탈환 | 역습 | partial | 108 | text | 예 | - | - |
| [kb2_022](kb2_022/) | 고양대 부근 전투 | 고지 방어·탈환 | 역습 | partial | 56 | text | **아니오** | plan_basis_outcome 1 | disguised_result 1 |
| [kb2_023](kb2_023/) | 백마고지 전투 | 고지 방어·탈환 | 지역방어 | partial | 48 | atlas+text | 예 | - | time_copied 1 |
| [kb2_024](kb2_024/) | 1090고지 부근 전투 | 고지 방어·탈환 | 지역방어 | partial | 15 | text | **아니오** | plan_combat_cue 1 | - |
| [kb2_026](kb2_026/) | 텍사스고지(689고지) 전투 | 고지 방어·탈환 | 역습 | success | 65 | text | 예 | - | time_copied 1, hidden_condition 1 |
| [kb2_028](kb2_028/) | 854고지 및 812고지 전투 | 고지 방어·탈환 | 지역방어 | failure | 56 | text | 예 | - | - |
| [kb2_029](kb2_029/) | 351고지 전투 | 고지 방어·탈환 | 지역방어 | failure | 97 | text | 예 | - | time_copied 1, hidden_condition 1 |
| [kb2_030](kb2_030/) | 미주리선(949고지-973고지-883고지) 방어전 | 고지 방어·탈환 | 역습 | failure | 94 | text | **아니오** | plan_basis_outcome 1 | time_copied 1 |
| [kb2_032](kb2_032/) | 1090고지 전투 | 고지 방어·탈환 | 역습 | success | 81 | text | **아니오** | plan_reactive 2 | time_copied 1, hidden_condition 2 |
| [kb2_033](kb2_033/) | 북진능선 전투 | 고지 방어·탈환 | 역습 | success | 31 | text | 예 | - | - |
| [kb2_034](kb2_034/) | 선우고지 전투 | 고지 방어·탈환 | 역습 | failure | 105.33 | text | 예 | - | time_copied 1 |
| [kb2_035](kb2_035/) | 퀸고지(250고지)-박고지(199고지) 전투 | 고지 방어·탈환 | 지역방어 | partial | 90 | text | 예 | - | time_copied 1, disguised_result 1 |
| [kb2_037](kb2_037/) | 화살머리고지(281고지) 전투 | 고지 방어·탈환 | 역습 | success | 72 | text | 예 | - | - |
| [kb2_040](kb2_040/) | 425고지 및 406고지 전투 | 고지 방어·탈환 | 지역방어 | partial | 65 | text | 예 | - | - |
| [kb2_043](kb2_043/) | 유곡리 전투 | 고지 방어·탈환 | 지역방어 | partial | 60 | text | **아니오** | plan_reactive 2 | disguised_result 1, time_copied 1 |
| [kb2_136](kb2_136/) | 사천강 혼비고지 전투 | 고지 방어·탈환 | 지역방어 | success | 19 | text | **아니오** | plan_basis_outcome 1 | hidden_condition 1 |
