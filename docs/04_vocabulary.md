# 열거값 사전

50건 데이터에서 자동으로 뽑았다. 값 옆 숫자는 50건 전체에서 나온 횟수다. 스키마가 허용하지만 데이터에 한 번도 나오지 않은 값은 `schema/*.schema.json`의 enum에서 확인한다.

## 과업 동사 `order.execution.tasks[].items[].verb`

역습 69 · 탈취 58 · 방어 56 · 점령 53 · 화력지원 40 · 확보 31 · 고수 25 · 경계 19 · 차단 17 · 저지 15 · 공격 12 · 지연 8 · 초월 8 · 철수 6 · 엄호 6 · 화력공격 5 · 후속지원 3 · 격퇴 3 · 소탕 3 · 견제 3 · 고착 2 · 후속인수 2 · 정찰 1 · 우회 1 · 격멸 1

## 과업 시점 `tasks[].items[].timing`

즉시 245 · 명에 의해 112 · 이어서 90

## 임무 동사 `order.mission.task_verb`

탈취 20 · 방어 18 · 저지 4 · 역습 4 · 지연 2 · 고수 2

## 편성 그룹 종류 `task_organization.groups[].kind`

기동 115 · 예비 50 · 화력지원 29 · 경계 18

## 배치 종류 `tasks[].deploy.kind`

진지 76 · 예비진지 50 · 공격대기지점 46 · 화력지원진지 25 · 전초 9 · 집결지 1

## 진지 준비 `preparation` (deploy·지형·적·통제수단 합계)

hasty 264 · deliberate 168 · fortified 144 · none 62

## 통제수단 종류 `coordinating.control_measures[].kind`

route 97 · battle_position 69 · boundary 57 · objective 56 · engagement_area 52 · assembly_area 34 · contact_point 29 · line_of_departure 27 · attack_position 25 · phase_line 17 · outpost 14 · other 11 · passage_point 11 · target 10 · limit_of_advance 8 · axis 2 · checkpoint 2

## 적 행동 mode `scenario.enemy_plan.groups[].items[].mode`

attack 160 · withdraw 112 · hold 108 · bombard 92 · counterattack 76 · reinforce 55 · fix 17 · infiltrate 16 · pursue 10

## 적 행동 시점 `enemy_plan…items[].timing`

계획 296 · 조건 259 · 이어서 91

## 상급 규칙 mode `higher_rules[].action.mode`

hold 32 · counterattack 22 · bombard 21 · attack 14 · reinforce 11 · withdraw 3 · fix 1

## 상급 규칙 시점 `higher_rules[].timing`

계획 57 · 조건 47

## 외생 사건 `scenario.exogenous[].kind`

night 158 · air_window 120 · dawn 62 · weather 11 · other 4 · fog 3 · flood 1

## 부대 병종 `type` (가용·적·숨은 적 합계)

infantry 374 · artillery 103 · armor 31 · mortar 18 · recon 17 · aviation 11 · marine 10 · antitank 5 · engineer 3 · other 2

## 부대 제대 `echelon` (가용·적·숨은 적 합계)

대대 324 · 연대 143 · 중대 74 · 소대 19 · 포대 6 · 사단 6 · 분대 1 · 여단 1

## 지원 관계 `available_forces[].relationship`

건제 167 · 직접지원 48 · 일반지원 32 · 배속 25 · 작전통제 10

## 적 태세 `enemy_forces[].posture`

방어 106 · 공격준비 49 · 예비 29 · 이동 22 · 미상 5

## 지형지물 종류 `terrain.features[].kind`

hill 379 · town 168 · river 52 · ridge 38 · area 31 · other 22 · valley 17 · crossing 16 · pass 8 · bridge 6 · lake 4

## 도로·통로 종류 `terrain.routes[].kind`

road 76 · ridge 50 · trail 25 · valley 8 · rail 2

## 시작 명암 `input.conditions.light`

day 20 · night 15 · dawn 8 · dusk 7

## 사건 type이 쓰인 곳

| 쓰인 곳 | time_elapsed | losses_exceed | strength_in_area |
|---|---|---|---|
| 지연 disengage |  | 8 |  |
| 아군 명에 의해 trigger |  | 50 | 73 |
| 예비 투입 commit |  | 22 | 30 |
| 시간계획 event | 149 | 1 | 1 |
| 임무 when | 50 |  |  |
| 적 계획 start | 296 |  |  |
| 적 조건 trigger |  | 164 | 110 |
| 종료 조건 |  | 142 |  |
| 상급 규칙 trigger | 57 | 17 | 39 |
