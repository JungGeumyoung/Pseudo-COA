# 교범 묶음

생성 모델의 입력에 넣는 교범 조항이다(파이프라인 조건 `D`, `DF`). 미 육군 공개 교범 원문(영문)에서 골랐다.

| 파일 | 내용 | 프롬프트에 들어가나 |
|---|---|---|
| `doctrine_pack.json` | 아래 전부. 파이프라인(`pipeline/prompt.py`)이 읽는다 | — |
| `verbs.md` | 한국어 과업 동사 ↔ 교범 정의(FM 3-90 부록 B 등) 32개 조항 | 예. 임무 유형과 상관없이 모두 |
| `mission_<유형>.md` | 임무 유형별 관련 조항 8개(지역방어·기동방어·공격·역습·지연·철수·추격·경계) | 예. 그 사례의 임무 유형 것만 |
| `doctrine_pack.json`의 `core` | 명령 양식·작전개념 일반 조항(FM 5-0, ADP 5-0) | 아니오. 참고용 |

## 고른 방법

- **동사 정의**: 한국어 과업 동사마다 뜻이 가장 가까운 교범 조항을 손으로 골랐다. 예를 들어 고수는 retain(FM 3-90 B-55), 고착은 fix(B-35)다. 정찰·격퇴·견제·공격·초월은 1:1로 맞는 조항이 없어 넣지 않았다.
- **임무 유형별 조항**: 교범 10종을 문단 단위로 자른 코퍼스(7,843문단)에서 임무 유형별 검색어(예: 지역방어는 area defense, engagement area, counterattack, reserve…)의 등장 횟수로 점수를 매겨 상위 8개를 골랐다. 한 교범이 절반을 넘지 않게 했다. 검색어는 각 `mission_<유형>.md`의 머리에 있다.

## 출처

`doctrine_pack.json`의 `sources`에 판본이 있다. FM 3-90 Tactics(2023), ADP 3-90 Offense and Defense(2019), FM 5-0(2024) 등이다. 모두 표지에 "Approved for public release; distribution is unlimited"가 적힌 공개 문서다.

## 바꾸려면

다른 교범(예: 한국군 교범)으로 바꾸려면 `doctrine_pack.json`을 같은 꼴로 만들면 된다. 꼴은 `{"verbs": [{verb, term, ref, text}], "missions": {유형: [{ref, text}]}}`다. `pipeline/prompt.py`의 `doctrine_text()`가 이 파일만 읽는다.
