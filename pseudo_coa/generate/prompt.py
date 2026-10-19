"""COA 생성 프롬프트를 조립한다: situation + (교범) + (pseudo-GT 예시) → 생성 모델에 줄 system, user.

입력 조건(cond)
  Z   situation과 명령 규칙만
  D   Z + 교범 묶음(doctrine/doctrine_pack.json: 과업 동사 정의 + 명령 구성 요소 + 임무 유형별 조항)
  F   Z + pseudo-GT 예시 k건(cases/<id>/의 situation.json → coa.json)
  DF  D + F   ← 기본값

예시(cases/<id>/situation.json + coa.json) 고르기: 같은 임무 유형을 먼저, 그 안에서 가용 부대 수와 적 부대 수가 비슷한 순. 동점은 대상 id를 시드로 섞는다.
50건 안의 사례를 대상으로 할 때(leave-one-out)는 그 사례와 같은 전투(제목의 지명·고지 번호가 겹침)를 예시에서 뺀다.
"""
import json
import os
import random
import re

from ..data import DOCTRINE_DIR, SCHEMA_DIR, list_cases, load_case

CONDITIONS = ["Z", "D", "F", "DF"]

TASK_VERBS = ["탈취", "확보", "점령", "고수", "소탕", "정찰", "격멸", "격퇴", "와해", "고착", "차단", "저지", "봉쇄", "무력화", "돌파", "우회", "견제",
              "공격", "역습", "방어", "지연", "추격", "철수", "이탈", "엄호", "경계", "차장", "후속지원", "후속인수", "초월", "화력지원", "화력공격"]
NOT_TASKS = ["증원", "재증원", "보강", "재편성", "재역습", "재탈환", "탈환", "집결", "이동", "교대", "투입", "진출"]
NEED = {"탈취": ["objective"], "확보": ["objective"], "점령": ["objective"], "고수": ["objective"], "소탕": ["objective"], "공격": ["objective"],
        "역습": ["objective", "route"], "방어": ["area"], "경계": ["area"], "차장": ["area"], "정찰": ["area"],
        "차단": ["line|area"], "저지": ["line|area"], "격멸": ["target_group|target_ref"], "격퇴": ["target_group|target_ref"],
        "와해": ["target_group|target_ref"], "고착": ["target_group|target_ref"], "봉쇄": ["target_group|target_ref"],
        "무력화": ["target_group|target_ref"], "우회": ["target_group|target_ref"], "견제": ["target_group|target_ref"],
        "돌파": ["axis_xy", "objective"], "지연": ["lines", "disengage"], "추격": ["limit_line"], "철수": ["destination"], "이탈": ["destination"],
        "엄호": ["covered_group"], "후속지원": ["followed_group"], "후속인수": ["followed_group"], "초월": ["passed_group", "passage_point"],
        "화력지원": ["supported_group", "target_ref"], "화력공격": ["target_ref"]}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


INDEX = list_cases()                 # cases/cases.csv 순서 (예시 고르기의 시드 섞기가 이 순서에 기댄다)
IDS = [r["id"] for r in INDEX]
ROW = {r["id"]: r for r in INDEX}


def order_schema():
    """구조화 출력에 쓸 order 스키마. CLI가 $schema 키를 받지 않으므로 뺀다."""
    return {k: v for k, v in load(os.path.join(SCHEMA_DIR, "coa.schema.json")).items() if not k.startswith("$")}


# ---------------------------------------------------------------- system
GEN_SYSTEM = """너는 연대 작전참모다. 주어진 상황(situation: 명령 시점에 연대가 받은 상급 임무·의도·부여 과업, 작전지역, 가용 부대, 지형 좌표, 적 정보)에서 연대장이 하달할 초기 배치 작전명령(방책) 하나를 JSON으로 쓴다. 이 명령은 그대로 시뮬레이터에 들어가 적의 실제 계획과 맞붙는다. 결과는 시뮬레이터가 낸다.

[명령의 형태]
 단계화하지 않은 초기 배치 명령 하나다. 구간 중의 결심은 '명에 의해' 대비 과업으로 미리 세운다.
 명령서 번호: 전투편성(task_organization) / 1. 상황 가.지형 나.적(최유력 방책 하나와 risk_point) 다.가정 / 2. 임무(한 문장: '아군 연대는 [언제] [어디서] [전술과업]하여 [목적]한다.') / 3. 실시 가.최종상태 나.작전개념(주력 main_effort, 예비와 투입 조건, 화력) 다.예하부대 과업 라.협조지시(시간계획, 통제수단). 4·5항은 쓰지 않는다.
 짧고 단정한 명령문체(~한다)로 쓰고 이유는 why·purpose·basis 필드에 둔다.

[전투편성]
 groups의 id는 G1, G2…, composition에는 situation.available_forces의 id를 쓰고 일부만 붙이거나 뗄 때 part에 적는다(예: part '제11중대' 또는 '-제11중대'). kind는 기동·예비·화력지원·경계. 기동·예비·경계 group은 모두 tasks에 과업과 deploy가 있어야 한다. 과업을 주지 않는 직접지원 포병·항공은 task_organization.text의 '지원:' 뒤에만 적어도 된다.

[과업]
 과업 동사(verb, mission.task_verb)는 다음만 쓴다: __VERBS__. __NOT__은 과업으로 쓰지 않는다.
 과업 문장(items[].text)은 그 동사로 끝낸다. group마다 항목 1~3개.
 동사별 필수 params: __NEED__.
 timing: '즉시'(명령과 함께 시작), '이어서'(같은 group의 바로 앞 항목이 끝나면. 첫 항목이 될 수 없다), '명에 의해'(대비 과업. trigger와 basis 필수). '즉시'·'이어서'에는 trigger를 쓰지 않고 문장에 '~하면' 같은 숨은 조건을 넣지 않는다.

[조건: 전투력만]
 '명에 의해' trigger, 예비 투입 조건(concept.reserve.commit), 지연의 disengage는 전투력 조건만 쓴다.
   losses_exceed {type, group, fraction(0~1], text}: 그 부대의 누적 손실 비율이 문턱을 넘음.
   strength_in_area {type, side(friendly|enemy), ref, min_echelon(소대·중대·대대·연대), text}: ref(지형·통제수단 id) 안에 그 규모 이상이 있음.
   여러 조건은 and로 묶되 모두 이 두 가지다. 시각·위치 도달·기상은 조건이 아니다. 시간계획(time_plan)의 계획 시각은 time_elapsed(value = D일 00:00부터 경과 시간)다.

[참조와 좌표]
 지형 참조 필드(*_ref, ref, terrain_refs, params의 objective·area·line·lines·route·destination·limit_line·passage_point)는 situation의 features·routes·impassable·boundaries id나 네가 control_measures에 정의한 id만 쓴다. 부대 참조는 group id, 적 id(situation.enemy_forces), 인접 부대 id만 쓴다. 정의되지 않은 id를 쓰지 않는다.
 캔버스는 200×200, 북쪽 +y, 1단위 = situation.terrain.scale_m_per_unit(m). 모든 좌표는 0~200. deploy에는 kind, 중심 xy, frontage_m, 가능하면 polygon과 중대 위치 elements를 쓴다. 경로는 능선·도로를 따라 경유점 3~8개로 쓴다.
 통제수단: 점 xy 1개, 선 2개 이상, 지역 3개 이상. 전투지경선, 접촉점, 목표, 교전지역, 공격개시선, 통과지점, 역습로 등을 필요에 따라 둔다.
 적 최유력 방책 steps에는 적 부대별 objective_ref, axis_xy, when, t를 쓴다. 주력은 group id 하나. 예비가 없으면 reserve.group을 '없음'으로 쓰고 이유를 priorities에 적는다.
 문장에서는 situation에 나온 이름(별칭)을 그대로 쓴다.

[출력] 문자열 안에 줄바꿈과 큰따옴표를 넣지 않는다. 한국어로 쓴다. 요청된 JSON 스키마(order 블록)만 출력한다.""".replace(
    "__VERBS__", ", ".join(TASK_VERBS)).replace("__NOT__", "·".join(NOT_TASKS)).replace(
    "__NEED__", "; ".join("%s=%s" % (v, "+".join(ps)) for v, ps in NEED.items()))


# ---------------------------------------------------------------- 교범
def doctrine_text(mission_type):
    pack = load(os.path.join(DOCTRINE_DIR, "doctrine_pack.json"))
    L = ["[교범 1: 과업 동사의 교범 정의] 한국어 과업 동사와 대응하는 미 육군 교범 정의다. 동사를 이 뜻대로 쓴다."]
    for v in pack["verbs"]:
        L.append("- %s (%s) [%s] %s" % (v["verb"], v["term"], v["ref"], v["text"]))
    L.append("\n[교범 2: 명령의 구성 요소] 임무 문장, 지휘관 의도·최종상태, 작전개념, 방책 진술·요도, 사실과 가정, 예비의 교범 정의다. order의 해당 칸을 이 뜻대로 쓴다.")
    for p in pack["core"]:
        L.append("- [%s] %s" % (p["ref"], p["text"]))
    L.append("\n[교범 3: 임무 유형 '%s' 관련 조항]" % mission_type)
    for p in pack["missions"].get(mission_type, []):
        L.append("- [%s] %s" % (p["ref"], p["text"]))
    return "\n".join(L)


# ---------------------------------------------------------------- 예시
_STOP = {"전투", "부근", "및", "제1차", "제2차", "고지"}


def _tokens(title):
    return {t for t in re.split(r"[\s\-()·,]+", re.sub(r"제\d차", "", title)) if t and t not in _STOP}


def related(a, b):
    """같은 전투를 다른 관점·구간으로 만든 사례인가(제목의 지명이나 고지 번호가 겹침)."""
    ta, tb = _tokens(ROW[a]["title"]), _tokens(ROW[b]["title"])
    nums = lambda s: set(re.findall(r"\d{3,4}", " ".join(s)))   # noqa: E731
    return bool(ta & tb) or bool(nums(ta) & nums(tb))


def pick_examples(situation, mission_type, k=3, exclude_id=None, seed=None):
    """situation과 비슷한 pseudo-GT k건의 id. exclude_id가 50건 안의 id면 그 사례와 같은 전투를 뺀다."""
    nf, ne = len(situation["available_forces"]), len(situation["enemy_forces"])
    rng = random.Random(seed if seed is not None else (exclude_id or "new"))
    pool = [x for x in IDS if x != exclude_id and not (exclude_id in ROW and related(exclude_id, x))]
    rng.shuffle(pool)

    def key(x):
        inp = load_case(x).situation
        return (ROW[x]["mission_type"] != mission_type,
                abs(len(inp["available_forces"]) - nf) + 0.5 * abs(len(inp["enemy_forces"]) - ne))
    return sorted(pool, key=key)[:k]


def _j(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"))


def build_user(situation, mission_type, cond="DF", k=3, exclude_id=None):
    """반환: (user 프롬프트, 고른 예시 id 목록)."""
    parts, ex = [], []
    if "D" in cond:
        parts.append(doctrine_text(mission_type))
    if "F" in cond:
        parts.append("[모범 답안 예시] 다른 전투의 상황과 그때 연대가 실제로 내린 명령(역사적 재구성)이다. 형식·상세 수준·조건 쓰는 법을 참고하되 "
                     "id와 좌표는 이번 상황의 것만 쓴다.")
        ex = pick_examples(situation, mission_type, k=k, exclude_id=exclude_id)
        for n, x in enumerate(ex, 1):
            a = load_case(x)
            parts.append("## 예시 %d (임무 유형: %s)\n[situation]\n%s\n[order]\n%s" % (n, ROW[x]["mission_type"], _j(a.situation), _j(a.coa)))
    parts.append("## 이번 과제 (임무 유형: %s)\n[situation]\n%s\n\n위 situation에 대한 order를 써라." % (mission_type, _j(situation)))
    return "\n\n".join(parts), ex
