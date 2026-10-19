"""situation 하나에서 COA(order)를 생성하고, 검사하고, 시뮬레이터 입력으로 만든다.

    # 50건 중 하나를 대상으로 (leave-one-out: 그 사례와 같은 전투는 예시에서 뺀다)
    python3 generation/generate_coa.py --case kb2_023 --out runs/kb2_023.DF.json --sim-out runs/kb2_023.sim.json

    # 새 상황 (input 블록 꼴의 JSON)
    python3 generation/generate_coa.py --situation my_situation.json --mission-type 지역방어 --out runs/new.json

    # 모델 없이 프롬프트만 보기
    python3 generation/generate_coa.py --case kb2_023 --dry-run > prompt.txt

흐름
  1. situation   data/situations/<id>.json의 input (또는 --situation 파일)
  2. 프롬프트    generation/prompt.py: system(명령 규칙) + user(교범 + pseudo-GT 예시 + situation). --cond로 고른다
  3. 생성        generation/backends.py: --backend claude:<model>:<effort> (Claude Code CLI) 또는 openai:<base_url>|<model> (vLLM 등)
  4. 검사        tools/validate_order.py: 오류가 있으면 시뮬레이션하지 않는다
  5. 시뮬레이터 입력  tools/case_io.py sim_view: 사례의 input + 새 order + scenario (50건 사례일 때만. 새 상황은 scenario가 없다)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from prompt import CONDITIONS, GEN_SYSTEM, ROW, build_user, load, order_schema  # noqa: E402
from validate_order import validate  # noqa: E402
from case_io import sim_view  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--case", help="50건 중 사례 id (예: kb2_023)")
    src.add_argument("--situation", help="input 블록 꼴 JSON 파일 ({'input': …} 또는 input 자체)")
    ap.add_argument("--mission-type", help="지역방어·기동방어·공격·역습·지연·철수·추격·경계. --case면 생략 가능")
    ap.add_argument("--cond", default="DF", choices=CONDITIONS)
    ap.add_argument("--k", type=int, default=3, help="예시 수")
    ap.add_argument("--backend", default="claude:claude-sonnet-5-5:medium")
    ap.add_argument("--out", help="결과 JSON (order, 검사 결과, 생성 메타)")
    ap.add_argument("--sim-out", help="시뮬레이터 입력 JSON (--case일 때만)")
    ap.add_argument("--dry-run", action="store_true", help="모델을 부르지 않고 system과 user 프롬프트를 출력")
    a = ap.parse_args()

    if a.case:
        s = load(os.path.join(ROOT, "data", "situations", a.case + ".json"))
        situation, mt, exclude = s["input"], a.mission_type or s["mission_type"], a.case
    else:
        s = load(a.situation)
        situation = s.get("input", s)
        mt = a.mission_type or s.get("mission_type")
        exclude = None
        if not mt:
            ap.error("--situation에는 --mission-type이 필요하다")
    user, examples = build_user(situation, mt, a.cond, k=a.k, exclude_id=exclude)
    if a.dry_run:
        print("=== system ===\n%s\n\n=== user (예시: %s) ===\n%s" % (GEN_SYSTEM, ", ".join(examples) or "없음", user))
        return

    from backends import make_backend
    order, meta = make_backend(a.backend).generate(GEN_SYSTEM, user, order_schema())
    if "order" in order and "task_organization" not in order:
        order = order["order"]
    case = load(os.path.join(ROOT, "data", "sim_cases", a.case + ".json")) if a.case else {"input": situation, "scenario": {}}
    err, warn = validate(case, order)
    rec = {"id": a.case, "mission_type": mt, "cond": a.cond, "examples": examples, "order": order,
           "validation": {"ok": not err, "errors": err, "warnings": warn}, "gen": meta}
    print("검사: 오류 %d, 경고 %d" % (len(err), len(warn)), file=sys.stderr)
    for e in err:
        print("  [error]", e, file=sys.stderr)
    out = json.dumps(rec, ensure_ascii=False, indent=1)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(out)
    else:
        print(out)
    if a.sim_out:
        if not a.case:
            ap.error("--sim-out은 --case일 때만 (새 상황에는 scenario가 없다)")
        if err:
            print("오류가 있어 시뮬레이터 입력을 쓰지 않는다", file=sys.stderr)
            sys.exit(1)
        json.dump(sim_view(case, order), open(a.sim_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.exit(0 if not err else 1)


if __name__ == "__main__":
    main()
