"""COA(order 블록) 검사: 그 사례의 시뮬레이터에 들어갈 수 있는가.

    from pseudo_coa import validate
    errors, warnings = validate("kb2_023", my_order)

검사는 둘이다.
  1. 구조: schema/coa.schema.json의 필수 키, 타입, 열거값(표준 라이브러리로 직접 검사)
  2. 의미: 참조 id가 그 사례에 정의되어 있는가, 동사와 params, 조건의 형태, 배치 좌표
오류(error)가 하나라도 있으면 시뮬레이션하지 않는다. 경고(warn)는 시뮬레이션은 되지만 교리상 지적이다.
"""
import os
import re

from .data import SCHEMA_DIR, Case, load_case, order_block, read_json
from .generate.prompt import NEED

CANVAS = 200
POWER = ("losses_exceed", "strength_in_area")
FORBIDDEN_RE = re.compile(r"재증원|재역습|재탈환|증원(?:한다|하여|하고|함)|보강(?:한다|하여)|재편성(?:한다|하여)")
COND_RE = re.compile(r"(?:하|되|받|오)면(?:\s|$)|올 때|할 때|될 때|경우")


def schema_errors(x, s, path="order"):
    """JSON Schema의 type·required·properties·items·enum·minItems·maxItems만 본다."""
    errs = []
    t = s.get("type")
    ok = {"object": isinstance(x, dict), "array": isinstance(x, list), "string": isinstance(x, str),
          "number": isinstance(x, (int, float)) and not isinstance(x, bool), "boolean": isinstance(x, bool)}.get(t, True)
    if not ok:
        return ["%s: %s이어야 함" % (path, t)]
    if "enum" in s and x not in s["enum"]:
        errs.append("%s: '%s'는 허용값이 아님 %s" % (path, x, s["enum"]))
    if t == "object":
        for k in s.get("required", []):
            if k not in x:
                errs.append("%s.%s: 필수 키 없음" % (path, k))
        for k, v in x.items():
            if k in s.get("properties", {}):
                errs += schema_errors(v, s["properties"][k], path + "." + k)
    if t == "array":
        if len(x) < s.get("minItems", 0):
            errs.append("%s: 항목이 %d개 이상이어야 함" % (path, s["minItems"]))
        if "maxItems" in s and len(x) > s["maxItems"]:
            errs.append("%s: 항목이 %d개 이하여야 함" % (path, s["maxItems"]))
        for i, v in enumerate(x):
            errs += schema_errors(v, s.get("items", {}), "%s[%d]" % (path, i))
    return errs


def validate(case, order):
    """case: Case 객체, 사례 id, 또는 {input, scenario} dict. order: order 블록(또는 {"order": …}).
    반환: (오류 목록, 경고 목록). 오류가 하나라도 있으면 시뮬레이션하지 않는다."""
    if isinstance(case, str):
        case = load_case(case)
    if isinstance(case, Case):
        case = {"input": case.situation, "scenario": case.scenario}
    order = order_block(order)
    err, warn = [], []
    s = read_json(os.path.join(SCHEMA_DIR, "coa.schema.json"))
    err += schema_errors(order, s)
    if err:
        return err, warn   # 구조가 깨지면 의미 검사는 하지 않는다
    I, Sc = case["input"], case["scenario"]
    T = I["terrain"]
    X = order["execution"]
    terrain = {f["id"] for k in ("features", "routes", "impassable") for f in T.get(k, [])} | {b["id"] for b in I["area_of_operations"]["boundaries"]}
    cms = {c["id"] for c in X["coordinating"]["control_measures"]}
    refs = terrain | cms
    forces = {f["id"] for f in I["available_forces"]}
    groups = {g["id"]: g["kind"] for g in order["task_organization"]["groups"]}
    adjacent = {a["id"] for a in I["higher_context"]["adjacent_units"]}
    hidden = {h["id"] for h in Sc.get("hidden_enemy", [])}
    enemy = {e["id"] for e in I["enemy_forces"]} | hidden   # 숨은 적은 정의된 id지만 명령이 알 수 없는 부대다(경고)

    def ref(v, where):
        if v and v not in refs:
            err.append("%s: 정의되지 않은 지형·통제수단 id '%s'" % (where, v))

    def grp(v, where, pool):
        if v and v not in pool:
            err.append("%s: 정의되지 않은 부대 id '%s'" % (where, v))
        elif v in hidden:
            warn.append("%s: 연대가 명령 시점에 몰랐던 적 '%s'를 참조" % (where, v))

    def power(ev, where):
        """반응 조건: 모든 사건(and 포함)이 전투력 조건이고 필수 필드가 찼는가."""
        if not ev:
            err.append("%s: 조건 없음" % where)
            return
        parts = [ev] + list(ev.get("and") or [])
        for k, e in enumerate(parts):
            if k == 0 and e.get("and") and not (e.get("group") or e.get("ref")):
                continue   # 바깥 사건을 묶음으로만 쓴 경우
            if e.get("type") not in POWER:
                err.append("%s[%d]: 반응 조건은 losses_exceed·strength_in_area만 (지금 %s)" % (where, k, e.get("type")))
            elif e["type"] == "losses_exceed":
                if not (e.get("group") and 0 < (e.get("fraction") or 0) <= 1):
                    err.append("%s[%d]: losses_exceed에 group과 fraction(0~1] 필요" % (where, k))
                grp(e.get("group"), where, set(groups) | forces | adjacent | enemy)
            else:
                if not (e.get("side") in ("friendly", "enemy") and e.get("ref") and e.get("min_echelon")):
                    err.append("%s[%d]: strength_in_area에 side·ref·min_echelon 필요" % (where, k))
                ref(e.get("ref"), where)

    # 전투편성
    for g in order["task_organization"]["groups"]:
        for c in g["composition"]:
            grp(c.get("force"), "task_organization.%s" % g["id"], forces)
    tasked = {t["group"] for t in X["tasks"]}
    for gid, kind in groups.items():
        if kind in ("기동", "예비", "경계") and gid not in tasked:
            err.append("tasks: %s(%s)에 과업 없음" % (gid, kind))
    # 임무·개념
    ref(order["mission"].get("objective_ref"), "mission.objective_ref")
    C = X["concept"]
    grp(C.get("main_effort"), "concept.main_effort", groups)
    rv = C["reserve"]
    if rv.get("group") not in ("없음", "", None):
        grp(rv["group"], "concept.reserve.group", groups)
        ref(rv.get("position_ref"), "concept.reserve.position_ref")
        power(rv.get("commit"), "concept.reserve.commit")
    for pg in C["fire_support"].get("priority_groups", []):
        grp(pg, "fire_support.priority_groups", set(groups) | adjacent)
    for z in C["fire_support"].get("zone_refs", []):
        ref(z, "fire_support.zone_refs")
    for k, kt in enumerate(order["situation"]["terrain"]["key_terrain"]):
        ref(kt.get("ref"), "situation.key_terrain[%d]" % k)
    for k, st in enumerate(order["situation"]["enemy"]["most_likely_coa"]["steps"]):
        grp(st.get("group"), "most_likely_coa.steps[%d]" % k, enemy)
        ref(st.get("from_ref"), "most_likely_coa.steps[%d].from_ref" % k)
        ref(st.get("objective_ref"), "most_likely_coa.steps[%d].objective_ref" % k)
    # 과업
    for t in X["tasks"]:
        gid = t["group"]
        grp(gid, "tasks", groups)
        d = t["deploy"]
        ref(d.get("ref"), "tasks.%s.deploy.ref" % gid)
        for el in d.get("elements", []):
            ref(el.get("ref"), "tasks.%s.deploy.elements" % gid)
        for i, it in enumerate(t["items"]):
            w = "tasks.%s.items[%d]" % (gid, i)
            tm, p = it["timing"], it.get("params") or {}
            if tm == "명에 의해":
                power(it.get("trigger"), w + ".trigger")
                if not (it.get("basis") or "").strip():
                    warn.append("%s: '명에 의해' 과업에 basis(근거) 없음" % w)
            elif it.get("trigger"):
                err.append("%s: '%s' 과업에는 trigger를 쓰지 않음" % (w, tm))
            if tm == "이어서" and i == 0:
                err.append("%s: '이어서'는 첫 항목이 될 수 없음" % w)
            if tm in ("즉시", "이어서") and COND_RE.search(it["text"]):
                warn.append("%s: '%s' 문장에 숨은 조건 '%s'" % (w, tm, COND_RE.search(it["text"]).group(0).strip()))
            if FORBIDDEN_RE.search(it["text"]):
                warn.append("%s: 과업으로 쓰지 않는 표현 '%s'" % (w, FORBIDDEN_RE.search(it["text"]).group(0)))
            miss = [k for k in NEED.get(it["verb"], []) if not any(p.get(a) for a in k.split("|"))]
            if miss:
                err.append("%s: 동사 '%s'에 params %s 필요" % (w, it["verb"], ",".join(miss)))
            for k in ("objective", "area", "line", "route", "target_ref", "destination", "limit_line", "passage_point"):
                ref(p.get(k), "%s.params.%s" % (w, k))
            for v in p.get("lines") or []:
                ref(v, w + ".params.lines")
            for k in ("covered_group", "followed_group", "passed_group", "supported_group"):
                grp(p.get(k), "%s.params.%s" % (w, k), set(groups) | adjacent)
            grp(p.get("target_group"), w + ".params.target_group", enemy)
            if p.get("disengage"):
                power(p["disengage"], w + ".params.disengage")
    # 협조지시
    for k, tp in enumerate(X["coordinating"]["time_plan"]):
        ev = tp["event"]
        if ev.get("type") != "time_elapsed" and not all(e.get("type") in POWER for e in [ev] + list(ev.get("and") or [])):
            err.append("time_plan[%d]: 시각(time_elapsed) 또는 전투력 조건이어야 함" % k)
    for c in X["coordinating"]["control_measures"]:
        for tr in c.get("terrain_refs", []):
            if tr not in terrain:
                err.append("control_measures.%s.terrain_refs: 정의되지 않은 지형 id '%s'" % (c["id"], tr))
    # 좌표
    def xys(x, path):
        if isinstance(x, list) and len(x) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in x):
            yield path, x
        elif isinstance(x, list):
            for i, v in enumerate(x):
                yield from xys(v, "%s[%d]" % (path, i))
        elif isinstance(x, dict):
            for k, v in x.items():
                if k in ("xy", "polygon", "axis_xy", "line") or isinstance(v, (dict, list)):
                    yield from xys(v, path + "." + k)
    for path, p in xys(order, "order"):
        if not (0 <= p[0] <= CANVAS and 0 <= p[1] <= CANVAS):
            err.append("%s: 좌표 %s가 캔버스(0~%d) 밖" % (path, p, CANVAS))
    return err, warn
