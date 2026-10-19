# 사례 목록과 품질 표시

`index.jsonl`과 각 사례의 `checks`, `meta.semantic_audit`에서 뽑았다. 50건 모두 `sim_projectable`(시뮬레이터가 읽을 수 있는 구조)은 참이다.

- **outcome_free**: 거짓이면 시나리오에 실제 결과가 섞였을 가능성을 규칙 검사가 표시한 것이다. 보정(calibration) 기준선에서는 빼거나 해당 항목을 확인하고 쓴다.
- **의미 검사 지적**: Sonnet이 시나리오 항목을 실제 경과와 대조해 지적한 수(time_copied: 실제 시각을 계획으로 옮김, disguised_result: 결과를 계획처럼 씀, hidden_condition: 숨은 조건). 사람이 확인하지 않은 지적이다.

| id | 전투 | 범주 | 임무 | 결과 | 시간(h) | 좌표 | outcome_free | 규칙 검사 표시 | 의미 검사 지적 |
|---|---|---|---|---|---|---|---|---|---|
| kb1_039 | 장림-운유산 전투 | 지연·철수·사주방어 | 지연 | partial | 24 | text | 예 | - | time_copied 2 |
| kb1_043 | 소양교 전투 | 하천선 방어·방어 후 역습 | 지역방어 | partial | 33 | text | 예 | - | disguised_result 1 |
| kb1_047 | 말고개 전투 | 고지 방어·탈환 | 지역방어 | success | 69 | text | 예 | - | time_copied 2, hidden_condition 1 |
| kb1_054 | 원미산-오류동 전투 | 고지 방어·탈환 | 지연 | success | 51 | text | 예 | - | time_copied 5, hidden_condition 1, disguised_result 1 |
| kb1_062 | 무극리 전투 | 하천선 방어·방어 후 역습 | 지역방어 | partial | 30 | atlas+text | **아니오** | plan_basis_outcome 1 | - |
| kb1_070 | 공주 전투 | 하천선 방어·방어 후 역습 | 지역방어 | failure | 54 | text | 예 | - | - |
| kb1_071 | 대평리 전투 | 하천선 방어·방어 후 역습 | 지역방어 | failure | 84.5 | text | **아니오** | plan_basis_outcome 1 | time_copied 1, disguised_result 1 |
| kb1_080 | 함창 전투 | 고지 방어·탈환 | 지역방어 | success | 35 | text | 예 | - | - |
| kb1_083 | 권빈리 전투 | 고지 방어·탈환 | 지역방어 | success | 66 | text | **아니오** | plan_combat_cue 2 | hidden_condition 2 |
| kb1_085 | 낙정리 전투 | 하천선 방어·방어 후 역습 | 지역방어 | success | 68 | text | 예 | - | - |
| kb1_086 | 의성 전투 | 고지 방어·탈환 | 지역방어 | failure | 44 | text | 예 | - | disguised_result 1 |
| kb1_093 | 수암산-유학산 전투 | 고지 방어·탈환 | 공격 | success | 67 | text | 예 | org_uncovered 1, task_text_ending 1 | hidden_condition 1 |
| kb1_102 | 마산 서북방 전투 | 하천선 방어·방어 후 역습 | 지역방어 | success | 150 | text | **아니오** | plan_basis_outcome 1 | hidden_condition 1 |
| kb1_103 | 수암산 전투 | 능선 공격 | 공격 | failure | 84 | text | **아니오** | org_uncovered 1, plan_basis_outcome 1 | hidden_condition 1 |
| kb1_108 | 영천 전투 | 지연·철수·사주방어 | 역습 | success | 34 | text | 예 | - | - |
| kb1_136 | 개천-비호산 전투 | 고지 방어·탈환 | 지역방어 | partial | 52 | text | 예 | - | - |
| kb1_149 | 원주 전투 | 고지 방어·탈환 | 공격 | success | 102 | text | **아니오** | plan_reactive 1 | - |
| kb1_175 | 매봉-한석산 전투 | 능선 공격 | 공격 | success | 84 | text | 예 | - | hidden_condition 1 |
| kb1_185 | 924고지 전투 | 능선 공격 | 공격 | success | 128 | text | 예 | - | disguised_result 1 |
| kb1_186 | 884고지 전투 | 고지 방어·탈환 | 공격 | success | 83 | text | **아니오** | plan_basis_outcome 1 | - |
| kb1_187 | 피의 능선 전투 | 능선 공격 | 공격 | success | 101 | text | 예 | org_uncovered 1 | - |
| kb1_189 | 단장의 능선 전투 | 능선 공격 | 공격 | success | 72 | atlas+text | **아니오** | task_text_ending 1, plan_reactive 1 | - |
| kb1_190 | 백석산 전투 | 능선 공격 | 공격 | success | 32 | text | 예 | - | - |
| kb2_003 | 제1차 월비산 전투 | 능선 공격 | 공격 | success | 96 | text | 예 | - | - |
| kb2_005 | 금성천-교암산 전투 | 능선 공격 | 공격 | success | 108 | text | **아니오** | plan_reactive 1 | hidden_condition 1 |
| kb2_006 | 제2차 가칠봉 부근 전투 | 능선 공격 | 공격 | partial | 85 | text | 예 | - | - |
| kb2_008 | 281고지 및 395고지 전투 | 고지 방어·탈환 | 지역방어 | partial | 61 | text | **아니오** | plan_basis_outcome 1 | disguised_result 2 |
| kb2_009 | 제2차 월비산 전투 | 고지 방어·탈환 | 지역방어 | failure | 150 | text | **아니오** | plan_basis_outcome 1 | hidden_condition 1 |
| kb2_011 | 임진강 부근 전투 | 고지 방어·탈환 | 역습 | partial | 52 | text | **아니오** | plan_reactive 1 | hidden_condition 1 |
| kb2_013 | 두매리 전투 | 고지 방어·탈환 | 공격 | failure | 35 | text | 예 | - | - |
| kb2_017 | A고지 및 B고지 전투 | 고지 방어·탈환 | 공격 | success | 20.5 | text | **아니오** | plan_reactive 1 | time_copied 1, hidden_condition 1 |
| kb2_018 | 수도고지 및 지형능선 전투 | 고지 방어·탈환 | 지역방어 | partial | 86 | text | 예 | - | time_copied 1 |
| kb2_019 | 351고지 전투 | 고지 방어·탈환 | 역습 | success | 76 | text | 예 | - | - |
| kb2_020 | 벙커고지(122고지) 부근 전투 | 고지 방어·탈환 | 지역방어 | success | 76 | text | **아니오** | plan_basis_outcome 1 | disguised_result 1, time_copied 1 |
| kb2_021 | 피의고지 및 독수리고지 전투 | 고지 방어·탈환 | 역습 | partial | 108 | text | 예 | - | - |
| kb2_022 | 고양대 부근 전투 | 고지 방어·탈환 | 역습 | partial | 56 | text | **아니오** | plan_basis_outcome 1 | disguised_result 1 |
| kb2_023 | 백마고지 전투 | 고지 방어·탈환 | 지역방어 | partial | 48 | atlas+text | 예 | - | time_copied 1 |
| kb2_024 | 1090고지 부근 전투 | 고지 방어·탈환 | 지역방어 | partial | 15 | text | **아니오** | plan_combat_cue 1 | - |
| kb2_026 | 텍사스고지(689고지) 전투 | 고지 방어·탈환 | 역습 | success | 65 | text | 예 | - | time_copied 1, hidden_condition 1 |
| kb2_028 | 854고지 및 812고지 전투 | 고지 방어·탈환 | 지역방어 | failure | 56 | text | 예 | - | - |
| kb2_029 | 351고지 전투 | 고지 방어·탈환 | 지역방어 | failure | 97 | text | 예 | - | time_copied 1, hidden_condition 1 |
| kb2_030 | 미주리선(949고지-973고지-883고지) 방어전 | 고지 방어·탈환 | 역습 | failure | 94 | text | **아니오** | plan_basis_outcome 1 | time_copied 1 |
| kb2_032 | 1090고지 전투 | 고지 방어·탈환 | 역습 | success | 81 | text | **아니오** | plan_reactive 2 | time_copied 1, hidden_condition 2 |
| kb2_033 | 북진능선 전투 | 고지 방어·탈환 | 역습 | success | 31 | text | 예 | - | - |
| kb2_034 | 선우고지 전투 | 고지 방어·탈환 | 역습 | failure | 105.33 | text | 예 | - | time_copied 1 |
| kb2_035 | 퀸고지(250고지)-박고지(199고지) 전투 | 고지 방어·탈환 | 지역방어 | partial | 90 | text | 예 | - | time_copied 1, disguised_result 1 |
| kb2_037 | 화살머리고지(281고지) 전투 | 고지 방어·탈환 | 역습 | success | 72 | text | 예 | - | - |
| kb2_040 | 425고지 및 406고지 전투 | 고지 방어·탈환 | 지역방어 | partial | 65 | text | 예 | - | - |
| kb2_043 | 유곡리 전투 | 고지 방어·탈환 | 지역방어 | partial | 60 | text | **아니오** | plan_reactive 2 | disguised_result 1, time_copied 1 |
| kb2_136 | 사천강 혼비고지 전투 | 고지 방어·탈환 | 지역방어 | success | 19 | text | **아니오** | plan_basis_outcome 1 | hidden_condition 1 |
