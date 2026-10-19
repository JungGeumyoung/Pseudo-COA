# 사례 따라가기: kb2_023 백마고지 전투

사례 하나를 시뮬레이터가 읽는 순서대로 따라간다. 파일은 [`cases/kb2_023/`](../../cases/kb2_023/)이다. 약도와 명령서는 [`cases/kb2_023/README.md`](../../cases/kb2_023/README.md)에서 볼 수 있다.

| 항목 | 값 |
|---|---|
| 관점 | 국군 제9사단 **제30연대**, 지역방어 |
| 구간 | D일 06:00(적 공격준비사격 직전) ~ D+2일 06:00, `start_t = 6`, `horizon_h = 48` → 끝 t = 54 |
| 좌표 | 아틀라스 측정 + 서술. 395고지 정상 = (100, 100), 1단위 = 100m |
| 실제 결과 | partial (`meta.outcome.label`). 평가 때만 본다 |

## 1. 맵 — `input.terrain`

지형지물 14개다. 주요 지형:

| id | 이름 | kind | xy | preparation |
|---|---|---|---|---|
| `H395` | 395고지(주봉) | hill | (100, 100) | deliberate |
| `H_HR` | 화랑고지(전초) | hill | (112, 109.5) | hasty |
| `H_NM` | 무명고지 | hill | (106, 104) | |
| `R_E` | 395고지 동측 구릉 | ridge | (127, 88) | deliberate |
| `H500` | 500고지(적 진지) | hill | (119, 122) | fortified |
| `X_YG` | 역곡천 도하점 | crossing | (111, 74) | |

`impassable`의 `IMP_FLOOD`(역곡천 범람 구역)은 `active: "구간 중 발생"`, `gap_at: [111, 74]`이다. 처음에는 꺼져 있고, 외생 사건이 켠다(§6).

## 2. 아군 배치 — `order.task_organization` + `order.execution.tasks[].deploy`

| group | label | kind | composition | 유닛(§3 환산) | deploy |
|---|---|---|---|---|---|
| G1 | 제1대대(+제11중대) | 기동 | F1 + F3의 제11중대 | 15 + 4 = 19 | 진지 (104, 93), deliberate |
| G2 | 제2대대 | 기동 | F2 | 15 | 진지 (127, 88), deliberate |
| G3 | 제3대대(-) | 예비 | F3 − 제11중대 | 15 − 4 = 11 | 예비진지 (126.6, 62.2), hasty |
| G4 | 제53전차중대 | 화력지원 | F4 (armor 중대) | 전차 3 | 화력지원진지 (106, 84), hasty |

F5(사단 포병)는 group이 아니다. `task_organization.text`의 "지원:"에만 있으므로 화력 이벤트로 처리한다.

## 3. 적 배치 — `input.enemy_forces` + `scenario.hidden_enemy`

| id | 부대 | 규모 | 태세 | xy |
|---|---|---|---|---|
| E1 | 적 제340연대 1개 대대(화랑고지 축) | 대대 | 공격준비 | (121, 124) |
| E2 | 적 제340연대 1개 대대(주봉 축) | 대대 | 공격준비 | (105, 125) |
| E3 | 적 제340연대 1개 대대(연대 예비) | 대대 | 예비 | (131, 134) |
| E4 | 적 제341연대 | 연대 | 방어 | (88, 130) |
| E5 | 적 제342연대 | 연대 | 예비 | (104.8, 168.4) |
| E6 | 적 제114사단 포병 | 대대(artillery) | 공격준비 | (110, 150) |
| **HE1** | 적 제334연대 (숨은 적) | 연대 | — | (120, 175) |

HE1은 연대가 명령 시점에 몰랐던 부대다. 생성 모델에게는 보이지 않지만 시뮬레이터에는 처음부터 있다.

## 4. 규칙 — 누가 언제 움직이나

### 아군 (`order.execution.tasks[].items[]`)
```
G1  즉시      점령  objective=H395
    즉시      경계  area=H_HR              (제11중대로 화랑고지 전초)
    이어서    고수  objective=H395          ← H395 점령이 끝나면
G2  즉시      점령  objective=R_E
    이어서    방어  area=R_E
G3  즉시      점령  objective=CM_AA         (예비진지)
    명에 의해 역습  objective=H395, route=CM_RT
              trigger: strength_in_area(side=enemy, ref=H395, min_echelon=중대)
G4  즉시      화력지원 supported_group=G1, target_ref=CM_EA1
```
G3의 역습 조건은 `concept.reserve.commit`과 같다. 주봉 반경 500m 안에 적이 중대 규모(환산 4유닛) 이상 들어오면 G3가 `CM_RT` 경유점을 따라 역습한다.

### 상급 (`input.higher_context.higher_rules`)
```
ADJ2(제28연대, 사단 예비)  조건  counterattack → H395, axis_xy 6점(남쪽에서 도하점 X_YG 경유)
    trigger: strength_in_area(side=enemy, ref=H395, min_echelon=대대)
```
적이 대대 규모(15유닛) 이상으로 주봉에 들어오면 사단 예비가 역습한다. 연대 예비(중대 기준)보다 문턱이 높다.

### 적 (`scenario.enemy_plan`)
```
E6   계획 t=6      bombard → H395
     이어서        bombard → H_HR
E1   계획 t=19.25  attack → H_HR     repeat {max:3, interval_h:2.7}
     이어서        attack → H_NM
E2   계획 t=19.25  attack → H395     repeat {max:3, interval_h:2.7}
     조건          hold   H_NM       trigger: strength_in_area(enemy, H_NM, 중대)
E3   계획 t=6      hold   H500
     조건          reinforce → H_NM  trigger: losses_exceed(E1, 0.3)
E4   계획 t=6      fix    H395
E5   계획 t=6      hold   H_HS
HE1  조건          attack → H_HR     trigger: losses_exceed(E2, 0.5)
     이어서        attack → H395
     계획 t=53.5   attack → H395
```
- E1·E2는 결과와 상관없이 t=19.25(D일 19:15, 야간)에 공격을 시작하고, 2.7시간 간격으로 세 번까지 되풀이한다.
- E3는 E1의 손실이 30%를 넘으면 증원한다. HE1은 E2의 손실이 50%를 넘으면 투입된다. 둘 다 결과가 아니라 **전투력 상태**로 정한 반응이다.
- HE1의 마지막 '계획' 항목(t=53.5)은 의미 검사가 `time_copied`(실제 5차 공격 시각을 계획으로 옮김)로 지적했다. 이런 지적은 [`cases/README.md`](../../cases/README.md)에 사례별로 있다.

## 5. 협조지시

- 시간계획: 진지 점령과 예비 역습 준비를 t=6까지 완료한다. 시작 시각과 같으므로 배치된 상태로 시작한다는 뜻이다.
- 통제수단 8개: 대대 전투지경선 `CM_BL12`, 접촉점 `CM_CP12`, 교전지역 `CM_EA1`(다각형, 화력 집중 지역), 전초 `CM_OP`, 예비진지 `CM_AA`, 역습 공격개시선 `CM_LD`, 통과지점 `CM_PP`, 역습로 `CM_RT`(경유점 7개).

## 6. 외생 사건 — `scenario.exogenous`

| t | kind | duration_h | ref | 효과 |
|---|---|---|---|---|
| 6 | dawn | 1 | | 여명 |
| 6 | flood | 48 | `IMP_FLOOD` | 역곡천 범람. 도하점 `gap_at`만 통과 → 사단 예비 ADJ2와 연대 예비 G3의 역습로가 도하점 하나로 좁아진다 |
| 6.5 | air_window | 11.5 | | 주간 근접항공지원 가능 |
| 18.5 | night | 11.5 | | 야간 (적 1차 공격이 이 안에서 시작) |
| 30.5 | air_window | 11.5 | | |
| 42.5 | night | 11.5 | | |
| 53.5 | fog | 3 | `H395` | 주봉 일대 짙은 안개. 포병·항공 불가 |

## 7. 종료

- 끝 시각 t = 54.
- 조기 종료(`stop_conditions`), 둘 중 하나라도 참이면 끝:
  1. `losses_exceed(G1, 0.7)` — 주봉 수비 대대의 전투력이 30% 미만
  2. `losses_exceed(E2, 0.7)` **and** `losses_exceed(E1, 0.7)` — 적 공격 대대 둘 다 30% 미만

## 8. 평가 — `history` (시뮬레이션이 끝난 뒤에만 연다)

```
outcome_metrics.terrain_held_at_horizon = ["H395"]
key_times: t=6 공격준비사격과 수문 폭파 / t=19.25 1차 공격 / t=24.67 무명고지 피탈
           t=43 화랑고지 피탈(추정) / t=46 제1대대 주봉 철수(추정) / t=48 제28연대 역습으로 주봉 회복(추정)
```
끝 시각에 H395는 아군(제28연대)이 쥐고 있고, 화랑고지와 무명고지는 적이 쥐고 있다. pseudo-GT order를 돌린 시뮬레이션이 대략 이 궤적을 내면 보정이 맞은 것이다. 두 가지를 본다. 주봉이 한 번 넘어갔다가 사단 예비 역습으로 돌아오는지, 그리고 전초가 먼저 떨어지는지다.

## 직접 돌려 보기
```bash
python -m pseudo_coa show kb2_023                     # 사례 요약
python -m pseudo_coa validate kb2_023                 # pseudo-GT 검사 → 오류 0
python -m pseudo_coa sim-input kb2_023 -o sim.json    # 시뮬레이터 입력
python -m pseudo_coa eval-target kb2_023 -o eval.json # 평가 기준
```
