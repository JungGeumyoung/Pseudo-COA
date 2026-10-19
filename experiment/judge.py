"""LLM 심사: situation과 order 하나를 주고 루브릭으로 채점한다(블라인드).
생성 order(4조건)와 pseudo-GT order(익명화본, 'GT')를 똑같은 프롬프트로 채점해, 생성물이 GT 수준에 얼마나 가까운지 본다.
심사자는 출처를 모른다. order 안의 '대대 세부 보충' 같은 재구성 흔적은 지워서 넘긴다.

    python3 experiment/judge.py --model claude-opus-5-5 --workers 4
출력 results/judge/<cond>/<id>.json
"""
import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import IDS, CONDITIONS, OUT, COA, pseudo_gt, load

sys.path.insert(0, COA)
from backends import ClaudeCLIBackend, BackendError, UsageLimitError  # noqa: E402

CRITERIA = [
    ("mission", "임무 부합", "상급 임무·의도·부여 과업을 달성하는 명령인가. 임무 문장의 과업·목적이 상급 의도와 맞는가."),
    ("terrain", "지형 활용", "핵심 지형과 접근로 판단이 맞고, 배치(좌표·정면·종심)가 지형과 작전지역 경계에 맞는가. 좌표를 실제로 확인하라."),
    ("enemy", "적 대응", "적 최유력 방책이 situation의 적 정보(위치·규모·태세)와 맞고, 배치·예비·대비 과업이 그 위험 시점(risk_point)에 대응하는가."),
    ("forces", "전투력 운용", "주력·예비·화력의 배분이 교리적으로 타당한가(주력 집중, 예비 보유와 위치, 지원 우선순위). 가용 부대를 빠짐없이 썼는가."),
    ("execution", "협조·실행성", "통제수단·시간계획·투입 조건이 구체적이고 서로 맞아서 그대로 실행(시뮬레이션)할 수 있는가. 참조 id가 정의되어 있는가."),
]
JUDGE_SYSTEM = ("너는 연대급 작전명령을 심사하는 교관이다. 명령 시점의 상황(situation)과 그 상황에서 작성된 초기 배치 작전명령(order) 하나를 받는다. "
                "결과(전투가 실제로 어떻게 됐는지)는 모른다고 가정하고, 명령 시점에 알 수 있던 정보만으로 명령의 질을 판단한다. "
                "항목마다 1~5점(1 결함이 심함, 3 무난함, 5 모범적)을 주고 근거를 한두 문장으로 쓴다. 마지막으로 전체 점수(1~10)와 가장 큰 강점·약점을 쓴다.\n"
                "[항목]\n" + "\n".join(" %s %s: %s" % (k, n, d) for k, n, d in CRITERIA) +
                "\n점수를 후하게 주지 말고 항목 사이에 차이를 두라. 한국어로 쓴다. 요청된 JSON 스키마만 출력한다.")
_C = {"type": "object", "required": ["score", "reason"], "properties": {"score": {"type": "integer", "minimum": 1, "maximum": 5}, "reason": {"type": "string"}}}
JUDGE_SCHEMA = {"type": "object", "required": [k for k, _, _ in CRITERIA] + ["overall", "strength", "weakness"],
                "properties": dict({k: _C for k, _, _ in CRITERIA},
                                   overall={"type": "integer", "minimum": 1, "maximum": 10}, strength={"type": "string"}, weakness={"type": "string"})}


def scrub(order):
    """재구성 흔적(대대 세부 보충 가정, 서술·상황도 언급)을 지워 출처를 숨긴다."""
    o = json.loads(json.dumps(order))
    o["situation"]["assumptions"] = [a for a in o["situation"].get("assumptions", [])
                                     if not re.search(r"보충|서술|상황도|아틀라스", a.get("text", "") + a.get("why", ""))]
    return o


def user_prompt(cid, order):
    j = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":"))  # noqa: E731
    return "[situation]\n%s\n\n[order]\n%s\n\n위 order를 심사하라." % (j(pseudo_gt(cid)["input"]), j(scrub(order)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default=None)
    ap.add_argument("--conds", default=",".join(CONDITIONS + ["GT"]))
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    ids = args.ids.split(",") if args.ids else IDS
    backend = ClaudeCLIBackend(model=args.model, effort=args.effort, max_budget_usd=5.0, timeout=1800)
    jobs = []
    for c in args.conds.split(","):
        os.makedirs(os.path.join(OUT, "judge", c), exist_ok=True)
        for i in ids:
            dst = os.path.join(OUT, "judge", c, i + ".json")
            src = os.path.join(OUT, "gen", c, i + ".json")
            if not os.path.exists(dst) and (c == "GT" or os.path.exists(src)):
                jobs.append((c, i))
    print("%d jobs (%s/%s)" % (len(jobs), args.model, args.effort), flush=True)

    def work(job):
        c, i = job
        order = pseudo_gt(i)["order"] if c == "GT" else load(os.path.join(OUT, "gen", c, i + ".json"))["order"]
        o, meta = backend.generate(JUDGE_SYSTEM, user_prompt(i, order), JUDGE_SCHEMA)
        o.update({"id": i, "cond": c, "judge": {"model": args.model, "effort": args.effort, "cost_usd": meta.get("cost_usd")}})
        json.dump(o, open(os.path.join(OUT, "judge", c, i + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return o

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(work, j): j for j in jobs}
        for f in as_completed(futs):
            c, i = futs[f]
            try:
                r = f.result()
                print("  [ok] %-3s %s overall %s $%.2f" % (c, i, r["overall"], r["judge"]["cost_usd"] or 0), flush=True)
            except UsageLimitError as e:
                print("  [LIMIT] %s" % e, flush=True)
                for g in futs:   # 아직 시작하지 않은 작업은 취소한다 (Python 3.8 호환)
                    g.cancel()
                break
            except BackendError as e:
                print("  [ERR] %s %s: %s" % (c, i, str(e)[:300]), flush=True)


if __name__ == "__main__":
    main()
