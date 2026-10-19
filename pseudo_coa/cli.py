"""python -m pseudo_coa <명령> …

  list         사례 목록                      list --mission-type 지역방어 --calibration-ok
  show         사례 하나 요약                  show kb2_023 [--real-names]
  validate     COA 검사                       validate kb2_023 my_coa.json | validate --all
  sim-input    시뮬레이터 입력 JSON            sim-input kb2_023 [--coa my_coa.json] [-o sim.json]
  eval-target  평가 기준(실제 경과) JSON       eval-target kb2_023 [-o eval.json]
  prompt       생성 프롬프트 (모델 호출 없음)   prompt kb2_023 [--cond DF] | prompt --situation s.json --mission-type 공격
  generate     COA 생성 → 검사 (→ 시뮬레이터 입력)
               generate kb2_023 --out my_coa.json [--sim-out sim.json] [--cond DF] [--backend claude:claude-sonnet-5-5:medium]
"""
import argparse
import json
import os
import sys

from .data import list_cases, load_case, order_block, read_json
from .validate import validate


def _write(obj, path):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(s + "\n")
    else:
        print(s)


def cmd_list(a):
    f = {}
    if a.mission_type:
        f["mission_type"] = a.mission_type
    if a.calibration_ok:
        f["calibration_ok"] = "true"
    if a.outcome:
        f["outcome"] = a.outcome
    rows = list_cases(**f)
    print("%-8s %-24s %-6s %-8s %5s  %s" % ("id", "전투", "임무", "결과", "시간h", "보정용"))
    for r in rows:
        print("%-8s %-24s %-6s %-8s %5s  %s" % (r["id"], r["title"][:22], r["mission_type"], r["outcome"], r["horizon_h"],
                                              "○" if r["calibration_ok"] == "true" else "-"))
    print("%d건" % len(rows))


def cmd_show(a):
    c = load_case(a.case)
    S, O = (c.situation_real, c.coa_real) if a.real_names else (c.situation, c.coa)
    sc = c.scenario
    print("%s  %s  (%s, 실제 결과 %s)" % (c.id, c.title if a.real_names else "[익명]", c.mission_type, c.meta["outcome"]["label"]))
    print("관점: %s | 구간 t=%s~%s (%sh)" % (S["perspective"]["unit"], sc["start_t"], sc["start_t"] + sc["horizon_h"], sc["horizon_h"]))
    print("상급 임무:", S["higher_context"]["higher_mission"])
    print("\n가용 부대:", ", ".join("%s %s(%s)" % (f["id"], f["unit"], f["echelon"]) for f in S["available_forces"]))
    print("알려진 적:", ", ".join("%s %s(%s)" % (e["id"], e["unit"], e["echelon"]) for e in S["enemy_forces"]))
    print("숨은 적:  ", ", ".join("%s(%s)" % (e["id"], e["echelon"]) for e in sc.get("hidden_enemy", [])) or "없음", " ← 생성 모델에는 보이지 않음")
    print("\n[pseudo-GT COA]")
    print("임무:", O["mission"]["text"])
    for t in O["execution"]["tasks"]:
        g = next(x for x in O["task_organization"]["groups"] if x["id"] == t["group"])
        items = "; ".join("%s %s" % (it["timing"], it["verb"]) for it in t["items"])
        print("  %-3s %-18s %-5s @%s  %s" % (g["id"], g["label"][:18], g["kind"], t["deploy"]["xy"], items))
    r = O["execution"]["concept"]["reserve"]
    print("예비 투입 조건:", (r.get("commit") or {}).get("text", "-"))
    print("\n파일: %s/{situation,coa,scenario,history,source}.json, README.md, map.svg" % os.path.relpath(c.dir))


def _load_order(path):
    return order_block(read_json(path))


def cmd_validate(a):
    if a.all:
        rows = list_cases()
        bad = 0
        for r in rows:
            err, _ = validate(r["id"], load_case(r["id"]).coa)
            if err:
                bad += 1
                print("%s: 오류 %d" % (r["id"], len(err)))
                for e in err:
                    print("  [error]", e)
        print("통과 %d / %d" % (len(rows) - bad, len(rows)))
        sys.exit(1 if bad else 0)
    c = load_case(a.case)
    order = _load_order(a.coa) if a.coa else c.coa
    err, warn = validate(c, order)
    print("%s: 오류 %d, 경고 %d" % (c.id, len(err), len(warn)))
    for e in err:
        print("  [error]", e)
    for w in warn:
        print("  [warn] ", w)
    sys.exit(1 if err else 0)


def cmd_sim_input(a):
    c = load_case(a.case)
    order = _load_order(a.coa) if a.coa else None
    if order is not None:
        err, _ = validate(c, order)
        if err:
            print("COA 검사 오류 %d건 — 시뮬레이터 입력을 만들지 않습니다. validate로 확인하세요" % len(err), file=sys.stderr)
            sys.exit(1)
    _write(c.sim_input(order), a.o)


def cmd_eval_target(a):
    _write(load_case(a.case).eval_target(), a.o)


def _target(a):
    if a.case:
        return a.case
    s = read_json(a.situation)
    a.mission_type = a.mission_type or s.get("mission_type")
    return s.get("input", s)


def cmd_prompt(a):
    from .generate import build_prompt
    system, user, ex = build_prompt(_target(a), a.cond, a.k, a.mission_type)
    print("=== system ===\n%s\n\n=== user (예시: %s) ===\n%s" % (system, ", ".join(ex) or "없음", user))


def cmd_generate(a):
    from .generate import generate_coa
    order, meta = generate_coa(_target(a), a.cond, a.k, a.mission_type, a.backend)
    if a.case:
        err, warn = validate(a.case, order)
    else:
        err, warn = validate({"input": _target(a), "scenario": {}}, order)
    print("검사: 오류 %d, 경고 %d" % (len(err), len(warn)), file=sys.stderr)
    for e in err:
        print("  [error]", e, file=sys.stderr)
    _write({"id": a.case, "cond": a.cond, "examples": meta.get("examples"), "order": order,
            "validation": {"ok": not err, "errors": err, "warnings": warn}, "gen": meta}, a.out)
    if a.sim_out and a.case and not err:
        _write(load_case(a.case).sim_input(order), a.sim_out)
    sys.exit(1 if err else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m pseudo_coa", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("list", help="사례 목록")
    p.add_argument("--mission-type")
    p.add_argument("--outcome", choices=["success", "partial", "failure"])
    p.add_argument("--calibration-ok", action="store_true", help="시뮬레이터 보정 기준선에 써도 되는 30건만")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("show", help="사례 하나 요약")
    p.add_argument("case")
    p.add_argument("--real-names", action="store_true", help="실명판으로 보기")
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("validate", help="COA 검사")
    p.add_argument("case", nargs="?")
    p.add_argument("coa", nargs="?", help="검사할 COA JSON. 없으면 pseudo-GT를 검사")
    p.add_argument("--all", action="store_true", help="pseudo-GT 50건 전체")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("sim-input", help="시뮬레이터 입력 JSON")
    p.add_argument("case")
    p.add_argument("--coa", help="넣을 COA JSON. 없으면 pseudo-GT")
    p.add_argument("-o", help="출력 파일 (없으면 표준출력)")
    p.set_defaults(fn=cmd_sim_input)

    p = sub.add_parser("eval-target", help="평가 기준 JSON (시뮬레이션이 끝난 뒤에만)")
    p.add_argument("case")
    p.add_argument("-o")
    p.set_defaults(fn=cmd_eval_target)

    for name, fn, h in (("prompt", cmd_prompt, "생성 프롬프트 보기 (모델 호출 없음)"), ("generate", cmd_generate, "COA 생성")):
        p = sub.add_parser(name, help=h)
        p.add_argument("case", nargs="?", help="50건 중 사례 id")
        p.add_argument("--situation", help="새 상황 JSON (input 블록 또는 {'input': …})")
        p.add_argument("--mission-type")
        p.add_argument("--cond", default="DF", choices=["Z", "D", "F", "DF"], help="Z 규칙만 / D +교범 / F +예시 / DF +교범+예시")
        p.add_argument("-k", type=int, default=3, help="예시 수")
        if name == "generate":
            p.add_argument("--backend", default="claude:claude-sonnet-5-5:medium",
                           help="claude:<model>:<effort> 또는 openai:<base_url>|<model>")
            p.add_argument("--out", help="결과 JSON (없으면 표준출력)")
            p.add_argument("--sim-out", help="검사를 통과하면 시뮬레이터 입력도 쓴다 (사례 id일 때만)")
        p.set_defaults(fn=fn)

    a = ap.parse_args(argv)
    if not getattr(a, "fn", None):
        ap.print_help()
        return
    if a.cmd == "validate" and not (a.all or a.case):
        ap.error("validate: 사례 id 또는 --all")
    if a.cmd in ("prompt", "generate") and not (a.case or a.situation):
        ap.error("%s: 사례 id 또는 --situation" % a.cmd)
    a.fn(a)
