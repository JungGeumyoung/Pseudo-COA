# Pseudo-COA

6·25전쟁 연대급 전투 50건으로 만든 **COA(방책) 생성·시뮬레이션용 데이터셋**과 도구다.

각 전투마다 세 가지가 들어 있다.
- 지휘관이 명령을 내리던 순간의 **상황**
- 그때 실제로 내린 **명령**(pseudo-GT COA)
- 적의 실제 계획과 실제 경과

생성 모델에 새 상황을 주고 COA를 만들게 한 뒤, pysc2 시뮬레이터에서 같은 적과 싸워 보게 하는 데 쓴다.

```
 ① 상황 ──▶ [COA 생성 모델] ──▶ 새 COA ──▶ [검사] ──▶ [pysc2 시뮬레이터] ──▶ 결과
   ▲              ▲                                       ▲                       │
   │        ② pseudo-GT 예시                         ③ 적 계획·환경               ▼
   │        + 교범                                                     ③ 실제 결과와 비교
 data/situations   data/pseudo_gt, doctrine                  data/sim_cases
```

## 무엇이 들어 있나

| 폴더 | 내용 | 누가 쓰나 |
|---|---|---|
| [`data/situations/`](data/situations) | ① **상황** 50건: COA를 만들어야 할 상황(익명화) | 생성 모델 입력 |
| [`data/pseudo_gt/`](data/pseudo_gt) | ② **상황 + pseudo-GT COA** 50건: 실제로 내린 명령(익명화) | few-shot 예시 |
| [`data/sim_cases/`](data/sim_cases) | ③ **시뮬레이션 사례** 50건: ②의 실명판 + 적 계획·환경 + 실제 경과 | 시뮬레이터, 평가 |
| [`doctrine/`](doctrine) | 생성 모델 입력에 넣는 **교범** 조항(미 육군 공개 교범) | 생성 모델 입력 |
| [`generation/`](generation) | **COA 생성 스크립트**: 상황 + 교범 + 예시 → 생성 → 검사 → 시뮬레이터 입력 | 생성 담당 |
| [`tools/`](tools) | **검사기**(`validate_order.py`)와 **시뮬레이터 입력 만들기**(`case_io.py`) | 생성·시뮬레이션 담당 |
| [`tutorial/`](tutorial) | **JSON 양식 튜토리얼**: 사례 하나를 열어 보며 9단계로 익히기 | 처음 보는 사람 |
| [`docs/`](docs) | 자세한 설명(필드 사전, 시뮬레이터 규칙, 정할 것들) | 구현할 때 |
| [`experiment/`](experiment) | few-shot 생성 품질 실험과 결과 | 참고 |
| [`schema/`](schema), `sim_unit_table.json` | JSON Schema, 부대 규모 → SC2 유닛 수 환산표(초안) | 구현할 때 |

세 데이터 폴더의 차이와 사례 목록은 [`data/README.md`](data/README.md)에 있다.

## 처음 왔다면

1. **튜토리얼**을 돌려 본다. 30분이면 양식이 잡힌다.
   ```bash
   python3 tutorial/tutorial.py
   ```
2. [03. 사례 따라가기](docs/03_case_walkthrough.md): 백마고지 사례 하나를 시뮬레이터가 읽는 순서대로 따라간다.
3. 시뮬레이터를 만든다면 [02. 시뮬레이션 방법](docs/02_how_to_simulate.md)과 [05. 정해야 할 것들](docs/05_decisions_needed.md)을 읽는다.
4. COA를 생성한다면 [06. COA 생성](docs/06_coa_generation.md)을 읽는다.

Python 3.8 이상, 표준 라이브러리만 쓴다. 모델 호출에만 Claude Code CLI 로그인이나 OpenAI 호환 서버가 필요하다.

## 자주 쓰는 명령

```bash
# pseudo-GT 50건이 검사를 통과하는지
python3 tools/validate_order.py --all

# COA 생성 → 검사 → 시뮬레이터 입력
python3 generation/generate_coa.py --case kb2_023 --dry-run > prompt.txt         # 모델 없이 프롬프트만 보기
python3 generation/generate_coa.py --case kb2_023 --out runs/kb2_023.json --sim-out runs/kb2_023.sim.json

# 다른 곳에서 만든 COA를 검사하고 시뮬레이터 입력으로
python3 tools/validate_order.py data/sim_cases/kb2_023.json my_order.json
python3 tools/case_io.py sim  data/sim_cases/kb2_023.json --order my_order.json > sim_input.json

# 평가 기준(실제 경과) 꺼내기 — 시뮬레이션이 끝난 뒤에만
python3 tools/case_io.py eval data/sim_cases/kb2_023.json > eval_target.json
```

## 꼭 지킬 규칙 세 가지

1. **새 COA가 바꾸는 것은 `order` 하나뿐이다.** 상황(`input`)과 적·환경(`scenario`)은 사례마다 고정이다.
2. **생성 모델에는 ①과 ②만 준다.** ③의 `scenario`에는 연대가 몰랐던 적이 있고, `history`에는 실제 결과가 있다. `history`는 시뮬레이터에도 주지 않고 평가에만 쓴다.
3. **조건은 전투력으로만 쓴다.** 예비 투입이나 적의 반응은 "어느 부대의 손실이 몇 %를 넘으면"(`losses_exceed`)이나 "어느 지역에 적이 어느 규모 이상 있으면"(`strength_in_area`)으로만 쓴다. 시각(`time_elapsed`)은 조건이 아니라 일정이다. 결과는 시뮬레이터가 내야 하기 때문이다.

## 용어

| 용어 | 뜻 |
|---|---|
| COA | Course of Action, 방책. 여기서는 연대장의 **초기 배치 작전명령** 하나(`order`)로 표현한다 |
| pseudo-GT | 그 연대가 실제로 내린 명령을 전쟁사 서술에서 재구성한 것. 정답(최적해)이 아니라 **현실의 기준선**이다. 실제 결과는 성공·부분 성공·실패가 섞여 있다 |
| 상황 (`input`) | 명령 시점에 연대가 알던 것: 상급 임무·의도, 작전지역, 가용 부대(F1…), 지형(H395…), 적(E1…) |
| 시나리오 (`scenario`) | 시뮬레이터만 받는 것: 적의 실제 계획과 반응 규칙, 숨은 적(HE1…), 야간·안개 같은 환경, 시작·끝 시각 |
| 실제 경과 (`history`) | 실제로 일어난 일. 시뮬레이션 결과와 비교하는 데만 쓴다 |
| `t` | D일 00:00부터 지난 시간(h). D+1일 06:00 = 30 |
| 좌표 | 200×200 캔버스, 1단위 = 100m, 북쪽이 +y |
| 익명화 | 지명·부대명·날짜를 별칭으로 바꾼 것(`395고지` → `고지 A`). id와 좌표는 그대로다 |

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

## few-shot 생성 실험 결과

교범과 pseudo-GT 예시가 COA 생성에 도움이 되는지, 시뮬레이터 없이 먼저 본 실험이다. 결과는 [06. COA 생성](docs/06_coa_generation.md#실험-결과)과 [`experiment/results/REPORT.md`](experiment/results/REPORT.md)에 있다.

## 알아 둘 한계

- **좌표는 대부분 추정이다.** 지형지물 741개 중 703개가 서술에서 추정한 위치다. 상대 위치는 맞지만 수백 m 단위의 정밀도는 기대하지 않는다.
- **유닛 환산표는 보정 전 초안이다.** pseudo-GT를 돌려 실제 결과가 재현되도록 맞추는 것이 첫 작업이다([02 §7](docs/02_how_to_simulate.md#7-종료와-평가)).
- **20건은 시나리오에 실제 결과가 섞였을 수 있다**(`outcome_free = false`). 보정 기준선에서는 우선 빼는 것을 권한다([사례 목록](data/README.md)).
- **pseudo-GT는 사람이 전부 검토하지 않았다.** 사람이 확인한 것은 3건(kb2_023, kb1_062, kb1_189)과 kb2_006 일부다. 자동 의미 검사가 지적한 49개 항목(29건)도 확인 전이다.
- **`history`의 손실률은 약 40건에만 있다.**

## 문의와 수정 요청

틀리거나 부족한 곳은 사례 id와 JSON 경로(예: `kb2_023 scenario.enemy_plan.groups[6].items[2]`)를 적어 알려 준다. 스키마가 바뀌면 [CHANGELOG](CHANGELOG.md)에 남긴다.
