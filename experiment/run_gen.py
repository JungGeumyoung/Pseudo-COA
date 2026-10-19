"""50건 각각을 leave-one-out으로, 조건(Z, D, F, DF)별로 order를 생성한다.

    python3 experiment/run_gen.py --model claude-sonnet-5-5 --workers 4
    python3 experiment/run_gen.py --ids kb2_023 --conds Z        # 하나만 시험

출력 results/gen/<cond>/<id>.json  {"order": …, "gen": {model, cost_usd, duration_s, examples}}
이미 있는 파일은 건너뛴다.
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import IDS, CONDITIONS, GEN_SYSTEM, OUT, build_user, pick_examples, order_schema, COA

sys.path.insert(0, COA)
from backends import ClaudeCLIBackend, BackendError, UsageLimitError  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default=None)
    ap.add_argument("--conds", default=",".join(CONDITIONS))
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    ids = args.ids.split(",") if args.ids else IDS
    conds = args.conds.split(",")
    backend = ClaudeCLIBackend(model=args.model, effort=args.effort, max_budget_usd=5.0, timeout=1800)
    jobs = []
    for c in conds:
        os.makedirs(os.path.join(OUT, "gen", c), exist_ok=True)
        for i in ids:
            if not os.path.exists(os.path.join(OUT, "gen", c, i + ".json")):
                jobs.append((c, i))
    print("%d jobs (%s/%s)" % (len(jobs), args.model, args.effort), flush=True)

    def work(job):
        c, i = job
        o, meta = backend.generate(GEN_SYSTEM, build_user(i, c), order_schema())
        if "order" in o and "task_organization" not in o:
            o = o["order"]
        rec = {"id": i, "cond": c, "order": o,
               "gen": {"model": meta.get("model") or args.model, "effort": args.effort, "cost_usd": meta.get("cost_usd"),
                       "duration_s": meta.get("duration_s"), "usage": meta.get("usage"),
                       "examples": pick_examples(i) if "F" in c else []}}
        json.dump(rec, open(os.path.join(OUT, "gen", c, i + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return rec

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, j): j for j in jobs}
        for f in as_completed(futs):
            c, i = futs[f]
            try:
                r = f.result()
                print("  [ok] %-3s %s $%.2f %ss" % (c, i, r["gen"]["cost_usd"] or 0, r["gen"]["duration_s"]), flush=True)
            except UsageLimitError as e:
                print("  [LIMIT] %s" % e, flush=True)
                for g in futs:   # 아직 시작하지 않은 작업은 취소한다 (Python 3.8 호환)
                    g.cancel()
                break
            except BackendError as e:
                print("  [ERR] %s %s: %s" % (c, i, str(e)[:300]), flush=True)


if __name__ == "__main__":
    main()
