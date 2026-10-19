"""scores.jsonl과 judge/를 모아 results/REPORT.md를 쓴다. 조건 사이 비교는 사례 쌍 부트스트랩(평균 차이 95% 구간)."""
import collections
import glob
import json
import os
import random

from common import OUT, ROW, CONDITIONS

CRIT = ["mission", "terrain", "enemy", "forces", "execution"]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def boot(diffs, n=5000, seed=0):
    diffs = [d for d in diffs if d is not None]
    if len(diffs) < 3:
        return None
    rng = random.Random(seed)
    ms = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n)]


def fmt(x, d=2):
    return "—" if x is None else ("%.*f" % (d, x))


def main():
    S = collections.defaultdict(dict)
    for l in open(os.path.join(OUT, "scores.jsonl"), encoding="utf-8"):
        r = json.loads(l)
        S[r["cond"]][r["id"]] = r
    J = collections.defaultdict(dict)
    for p in glob.glob(os.path.join(OUT, "judge", "*", "*.json")):
        r = json.load(open(p, encoding="utf-8"))
        J[r["cond"]][r["id"]] = r
    conds = [c for c in CONDITIONS if c in S]
    L = ["# few-shot COA 생성 실험 결과", ""]
    n = {c: len(S[c]) for c in conds}
    L.append("사례 수: " + ", ".join("%s %d" % (c, n[c]) for c in conds) + "; 심사: " + ", ".join("%s %d" % (c, len(J[c])) for c in conds + ["GT"]))
    L.append("")
    # 1. 규칙 검사
    L += ["## 1. 규칙 검사 (validate_order)", "", "| 조건 | 유효(오류 0) | 평균 오류 | 평균 경고 | 오류 종류(건수) | 비용/건 |", "|---|---|---|---|---|---|"]
    for c in conds:
        rs = list(S[c].values())
        kinds = collections.Counter(k for r in rs for k in r["err_kinds"])
        L.append("| %s | %d/%d (%.0f%%) | %.2f | %.2f | %s | $%.2f |" % (
            c, sum(r["valid"] for r in rs), len(rs), 100 * mean([r["valid"] for r in rs]), mean([r["n_err"] for r in rs]),
            mean([r["n_warn"] for r in rs]), ", ".join("%s %d" % kv for kv in kinds.most_common(4)) or "-", mean([r["cost_usd"] for r in rs]) or 0))
    # 2. GT 일치
    M = [("place_km", "배치 거리 km ↓"), ("main_j", "주력 구성 J"), ("reserve_agree", "예비 유무 일치"), ("reserve_j", "예비 구성 J"),
         ("commit_type", "투입조건 type"), ("commit_ref", "투입조건 대상"), ("key_j", "핵심지형 J"), ("obj_j", "과업 지형 J"),
         ("mission_verb", "임무 동사"), ("mission_obj", "임무 목표"), ("verb_j", "동사 집합 J")]
    L += ["", "## 2. pseudo-GT와의 구조 일치", "", "높을수록 GT와 비슷하다(배치 거리만 낮을수록). J = Jaccard. "
          "배치 거리의 비교 기준(모든 부대를 GT 배치 중심 평균에 둠): %s km." % fmt(mean([r.get("place_km_naive") for r in S[conds[0]].values()])), "",
          "| 지표 | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
    for k, name in M:
        L.append("| %s | %s |" % (name, " | ".join(fmt(mean([(None if r.get(k) is None else float(r[k])) for r in S[c].values()])) for c in conds)))
    L.append("| group 수 (GT %.1f) | %s |" % (mean([r.get("n_groups_ref") for r in S[conds[0]].values()]),
                                             " | ".join(fmt(mean([r.get("n_groups") for r in S[c].values()]), 1) for c in conds)))
    L.append("| '명에 의해' 항목 수 | %s |" % " | ".join(fmt(mean([r.get("n_on_order") for r in S[c].values()]), 1) for c in conds))
    # 3. 심사
    jc = [c for c in conds + ["GT"] if J[c]]
    L += ["", "## 3. LLM 심사 (블라인드, 1~5점; 전체 1~10점)", "", "| 항목 | " + " | ".join(jc) + " |", "|---|" + "---|" * len(jc)]
    for k in CRIT + ["overall"]:
        L.append("| %s | %s |" % (k, " | ".join(fmt(mean([(r[k]["score"] if isinstance(r[k], dict) else r[k]) for r in J[c].values()])) for c in jc)))
    # 4. 쌍 비교
    def val(c, i, key):
        if key == "overall":
            r = J[c].get(i)
            return None if r is None else r["overall"]
        r = S[c].get(i)
        return None if r is None or r.get(key) is None else float(r[key])
    L += ["", "## 4. 조건 사이 차이 (같은 사례끼리 짝지어 평균 차이, 95% 부트스트랩 구간)", "",
          "| 비교 | 유효 | 배치 거리 km | 주력 J | 과업 지형 J | 심사 overall |", "|---|---|---|---|---|---|"]
    pairs = [("F", "Z"), ("DF", "D"), ("D", "Z"), ("DF", "F"), ("DF", "Z")] + [(c, "GT") for c in conds]
    for a, b in pairs:
        cells = []
        for key in ("valid", "place_km", "main_j", "obj_j", "overall"):
            if b == "GT" and key != "overall":
                cells.append("")
                continue
            src = J if key == "overall" else S
            ids = [i for i in src[a] if i in src[b]]
            d = [None if val(a, i, key) is None or val(b, i, key) is None else val(a, i, key) - val(b, i, key) for i in ids]
            ci = boot(d)
            cells.append("%s [%s, %s]" % (fmt(mean(d)), fmt(ci[0]), fmt(ci[1])) if ci else "—")
        L.append("| %s − %s | %s |" % (a, b, " | ".join(cells)))
    # 5. 심사 승률 vs GT
    L += ["", "## 5. 같은 사례에서 GT와 심사 overall 비교", "", "| 조건 | 이김 | 같음 | 짐 |", "|---|---|---|---|"]
    for c in conds:
        ids = [i for i in J[c] if i in J["GT"]]
        w = sum(J[c][i]["overall"] > J["GT"][i]["overall"] for i in ids)
        t = sum(J[c][i]["overall"] == J["GT"][i]["overall"] for i in ids)
        L.append("| %s | %d | %d | %d |" % (c, w, t, len(ids) - w - t))
    # 6. 임무 유형별
    mts = sorted({ROW[i]["mission_type"] for i in ROW}, key=lambda m: -sum(ROW[i]["mission_type"] == m for i in ROW))
    L += ["", "## 6. 임무 유형별 (유효율 / 심사 overall)", "", "| 임무 유형 (n) | " + " | ".join(jc) + " |", "|---|" + "---|" * len(jc)]
    for m in mts:
        ids = [i for i in ROW if ROW[i]["mission_type"] == m]
        cells = []
        for c in jc:
            v = "—" if c == "GT" else "%.0f%%" % (100 * (mean([S[c][i]["valid"] for i in ids if i in S[c]]) or 0))
            cells.append("%s / %s" % (v, fmt(mean([J[c][i]["overall"] for i in ids if i in J[c]]), 1)))
        L.append("| %s (%d) | %s |" % (m, len(ids), " | ".join(cells)))
    open(os.path.join(OUT, "REPORT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
