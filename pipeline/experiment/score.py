"""생성된 order를 자동 채점한다: 규칙 검사(validate_order)와 pseudo-GT(역사적 재구성)와의 구조 일치.

    python3 pipeline/experiment/score.py      # results/gen/*/*.json → results/scores.jsonl

지표 (모두 pseudo-GT order 대비, 높을수록 GT와 비슷)
  valid           validate_order 오류 0
  n_err, n_warn   오류·경고 수
  place_km        가용 부대(F*)마다 그 부대가 든 group의 deploy 중심 사이 거리 평균(km). 낮을수록 좋다
  place_km_naive  모든 부대를 GT 배치 중심들의 평균에 두었을 때의 거리(비교 기준: 지역만 맞히고 할당은 모르는 경우)
  main_j          주력 group 구성 부대 집합의 Jaccard
  reserve_agree   예비 보유 여부 일치
  reserve_j       예비 구성 Jaccard (둘 다 예비가 있을 때)
  commit_type     예비 투입 조건 type 일치, commit_ref: 조건 ref(또는 group) 일치
  key_j           핵심 지형(key_terrain ref) Jaccard
  obj_j           과업 params의 지형 참조(objective·area·line·lines·route·destination, 지형 id만) Jaccard
  mission_verb    임무 과업 동사 일치, mission_obj: 임무 objective_ref 일치
  verb_j          과업 동사 집합 Jaccard
"""
import glob
import json
import math
import os
import re
import sys

from common import OUT, HANDOFF, case

sys.path.insert(0, os.path.join(HANDOFF, "tools"))
from validate_order import validate  # noqa: E402


def jac(a, b):
    a, b = set(a), set(b)
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def force_xy(order):
    """F id → 그 부대가 든 group의 deploy 중심. 부대 전체가 든 group을 먼저, 없으면 일부가 든 group."""
    dep = {t["group"]: (t.get("deploy") or {}).get("xy") for t in order["execution"]["tasks"]}
    out = {}
    for whole in (True, False):
        for g in order["task_organization"]["groups"]:
            for c in g["composition"]:
                part = (c.get("part") or "").strip()
                if (not part or part.startswith("-")) == whole and c.get("force") not in out and dep.get(g["id"]):
                    out[c["force"]] = dep[g["id"]]
    return out


def group_forces(order, gid):
    for g in order["task_organization"]["groups"]:
        if g["id"] == gid:
            return {c["force"] for c in g["composition"]}
    return set()


def terrain_refs(order, terrain):
    s = set()
    for t in order["execution"]["tasks"]:
        for it in t["items"]:
            p = it.get("params") or {}
            for k in ("objective", "area", "line", "route", "destination", "limit_line", "passage_point"):
                if p.get(k) in terrain:
                    s.add(p[k])
            s |= {v for v in p.get("lines") or [] if v in terrain}
    return s


def has_reserve(o):
    return (o["execution"]["concept"]["reserve"].get("group") or "없음") not in ("없음", "")


def compare(c, gen):
    ref = c["order"]
    I = c["input"]
    terrain = {f["id"] for k in ("features", "routes", "impassable") for f in I["terrain"].get(k, [])} | \
              {b["id"] for b in I["area_of_operations"]["boundaries"]}
    km = c["meta"]["geo"]["scale_m_per_unit"] / 1000.0
    r = {}
    fr, fg = force_xy(ref), force_xy(gen)
    common = [f for f in fr if f in fg]
    r["place_km"] = sum(math.dist(fr[f], fg[f]) for f in common) / len(common) * km if common else None
    r["place_cov"] = len(common) / len(fr) if fr else None
    if fr:
        cx = [sum(p[0] for p in fr.values()) / len(fr), sum(p[1] for p in fr.values()) / len(fr)]
        r["place_km_naive"] = sum(math.dist(cx, p) for p in fr.values()) / len(fr) * km
    Cr, Cg = ref["execution"]["concept"], gen["execution"]["concept"]
    r["main_j"] = jac(group_forces(ref, Cr.get("main_effort")), group_forces(gen, Cg.get("main_effort")))
    r["reserve_agree"] = has_reserve(ref) == has_reserve(gen)
    if has_reserve(ref) and has_reserve(gen):
        r["reserve_j"] = jac(group_forces(ref, Cr["reserve"]["group"]), group_forces(gen, Cg["reserve"]["group"]))
        a, b = Cr["reserve"].get("commit") or {}, Cg["reserve"].get("commit") or {}
        r["commit_type"] = a.get("type") == b.get("type")
        if not r["commit_type"]:
            r["commit_ref"] = False
        elif a.get("type") == "strength_in_area":
            r["commit_ref"] = a.get("ref") == b.get("ref")
        else:   # losses_exceed: group id는 명령마다 다르므로 구성 부대로 비교
            r["commit_ref"] = group_forces(ref, a.get("group")) == group_forces(gen, b.get("group"))
    r["key_j"] = jac([k["ref"] for k in ref["situation"]["terrain"]["key_terrain"] if k.get("ref") in terrain],
                     [k["ref"] for k in gen["situation"]["terrain"]["key_terrain"] if k.get("ref") in terrain])
    r["obj_j"] = jac(terrain_refs(ref, terrain), terrain_refs(gen, terrain))
    r["mission_verb"] = ref["mission"].get("task_verb") == gen["mission"].get("task_verb")
    r["mission_obj"] = ref["mission"].get("objective_ref") == gen["mission"].get("objective_ref")
    verbs = lambda o: {it["verb"] for t in o["execution"]["tasks"] for it in t["items"]}  # noqa: E731
    r["verb_j"] = jac(verbs(ref), verbs(gen))
    r["n_groups"] = len(gen["task_organization"]["groups"])
    r["n_groups_ref"] = len(ref["task_organization"]["groups"])
    r["n_on_order"] = sum(1 for t in gen["execution"]["tasks"] for it in t["items"] if it.get("timing") == "명에 의해")
    r["n_cm"] = len(gen["execution"]["coordinating"]["control_measures"])
    return r


def err_kind(e):
    m = re.search(r"정의되지 않은|params .* 필요|반응 조건|trigger|첫 항목|캔버스|과업 없음|time_plan|필수|타입|enum|항목이", e)
    return m.group(0) if m else e[:30]


def main():
    rows = []
    for p in sorted(glob.glob(os.path.join(OUT, "gen", "*", "*.json"))):
        g = json.load(open(p, encoding="utf-8"))
        c = case(g["id"])
        err, warn = validate(c, g["order"])
        row = {"id": g["id"], "cond": g["cond"], "valid": not err, "n_err": len(err), "n_warn": len(warn),
               "err_kinds": sorted({err_kind(e) for e in err}), "errors": err[:20], "cost_usd": g["gen"].get("cost_usd")}
        try:
            row.update(compare(c, g["order"]))
        except Exception as e:  # 구조가 깨진 order
            row["compare_error"] = "%s: %s" % (type(e).__name__, e)
        rows.append(row)
    with open(os.path.join(OUT, "scores.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("scored %d" % len(rows))


if __name__ == "__main__":
    main()
