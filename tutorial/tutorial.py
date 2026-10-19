"""JSON 양식 튜토리얼: 사례 하나(kb2_023 백마고지)를 직접 열어 보며 양식을 익힌다.

    python3 tutorial/tutorial.py            # 처음부터 끝까지
    python3 tutorial/tutorial.py 4          # 4단계만

단계
  1. 파일 세 종류: inputs / anon / cases
  2. input: 생성 모델이 받는 상황
  3. order: 생성 모델이 쓰는 명령(COA)
  4. 조건과 timing: 언제 움직이나
  5. scenario: 시뮬레이터만 받는 것(적 계획, 숨은 적, 외생 사건, 종료)
  6. history: 평가에만 쓰는 실제 경과
  7. 유닛 환산: 제대 → 시뮬레이션 유닛 수
  8. 검사: 잘못된 order가 어떻게 걸리는가
  9. 파이프라인: 프롬프트 → 생성 → 검사 → 시뮬레이터 입력
표준 라이브러리만 쓴다.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from validate_order import validate  # noqa: E402
from case_io import sim_view, eval_view  # noqa: E402

CID = "kb2_023"


def load(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


def show(x, n=600):
    s = json.dumps(x, ensure_ascii=False)
    print("   " + (s if len(s) <= n else s[:n] + " …(%d자)" % len(s)))


def h(n, title):
    print("\n" + "=" * 70 + "\n%d. %s\n" % (n, title) + "=" * 70)


def step1():
    h(1, "파일 세 종류")
    full, an, inp = load("data", "cases", CID + ".json"), load("data", "anon", CID + ".json"), load("data", "inputs", CID + ".json")
    for name, x, use in (("data/inputs", inp, "생성 모델 입력(situation). 익명화"),
                         ("data/anon", an, "few-shot 예시 {input → order}. 익명화"),
                         ("data/cases", full, "전체: 시뮬레이터 입력과 평가 기준. 실명")):
        print("- %-12s 키 %s\n  %s" % (name, list(x.keys()), use))
    print("\n세 파일의 id·좌표는 같다. 익명화는 이름만 바꾼다(395고지 → %s)." %
          next(f["alias"] for f in full["input"]["terrain"]["features"] if f["id"] == "H395"))
    print("전체판의 블록: meta(출처·결과 요약, 아무에게도 주지 않음) / input / order / scenario / history / checks(자동 검사 결과)")


def step2():
    h(2, "input: 명령 시점의 상황")
    I = load("data", "inputs", CID + ".json")["input"]
    print("관점 부대:", I["perspective"]["alias"], "| 상급 임무:", I["higher_context"]["higher_mission"])
    print("부여 과업:", I["higher_context"]["assigned_task"])
    print("\n가용 부대(available_forces) — order의 전투편성이 이 id를 쓴다")
    for f in I["available_forces"]:
        print("   %-3s %-10s %s %s%s %s%%" % (f["id"], f["alias"], f["echelon"], f["type"], f["modifier"], f["strength_pct"]))
    print("\n지형(terrain.features) %d개 — order의 objective·area 등이 이 id를 쓴다. 좌표는 200×200 캔버스, 1단위 = %sm, 북쪽 +y" % (
        len(I["terrain"]["features"]), I["terrain"]["scale_m_per_unit"]))
    for f in I["terrain"]["features"][:5]:
        print("   %-8s %-8s %-8s xy=%s 준비=%s" % (f["id"], f["alias"], f["kind"], f["xy"], f.get("preparation", "")))
    print("\n적(enemy_forces) — 연대가 명령 시점에 알던 적만 있다")
    for e in I["enemy_forces"]:
        print("   %-3s %-10s %s %-9s 태세=%s xy=%s" % (e["id"], e["alias"], e["echelon"], e["type"], e["posture"], e["position"]["xy"]))
    print("\n상급·인접 부대의 조건부 행동(higher_rules) — 시뮬레이터가 실행한다")
    for r in I["higher_context"].get("higher_rules", []):
        print("   %s %s %s → %s | trigger: %s" % (r["unit"], r["timing"], r["action"]["mode"], r["action"]["objective_ref"], r["trigger"]["text"]))


def step3():
    h(3, "order: 생성 모델이 쓰는 COA")
    O = load("data", "anon", CID + ".json")["order"]
    print("명령서 번호와 키: 전투편성 task_organization / 1.상황 situation / 2.임무 mission / 3.실시 execution")
    print("\n전투편성:", O["task_organization"]["text"])
    for g in O["task_organization"]["groups"]:
        print("   %-3s %-14s %-5s composition=%s" % (g["id"], g["label"], g["kind"], g["composition"]))
    print("\n임무:", O["mission"]["text"], "| task_verb =", O["mission"]["task_verb"])
    C = O["execution"]["concept"]
    print("주력:", C["main_effort"], "| 예비:", C["reserve"]["group"], "| 예비 투입 조건:", C["reserve"]["commit"]["text"])
    print("\n예하부대 과업(tasks): group마다 배치(deploy)와 과업 항목(items)")
    for t in O["execution"]["tasks"]:
        d = t["deploy"]
        print("   %s deploy: %s xy=%s 정면 %sm" % (t["group"], d["kind"], d["xy"], d.get("frontage_m")))
        for it in t["items"]:
            print("      %-6s %-5s params=%s%s" % (it["timing"], it["verb"], it.get("params"),
                                                 "  trigger=" + it["trigger"]["text"] if it.get("trigger") else ""))
    print("\n통제수단(control_measures) — order 안에서 정의하고 참조한다")
    for c in O["execution"]["coordinating"]["control_measures"]:
        print("   %-8s %-18s 점 %d개" % (c["id"], c["kind"], len(c["xy"]) if isinstance(c["xy"][0], list) else 1))


def step4():
    h(4, "조건과 timing")
    print("아군 과업 timing:  즉시 = 명령과 함께 시작 / 이어서 = 같은 group 앞 항목이 끝나면 / 명에 의해 = trigger가 참이 되면")
    print("적 계획 timing:    계획 = start 시각에 / 이어서 / 조건 = trigger가 참이 되면")
    print("상급 규칙 timing:  계획 / 조건")
    print("\n반응 조건(trigger, reserve.commit, disengage)은 전투력 두 가지뿐이다:")
    show({"type": "losses_exceed", "group": "G1", "fraction": 0.4, "text": "제1대대 누적 손실 40% 초과"})
    show({"type": "strength_in_area", "side": "enemy", "ref": "H395", "min_echelon": "중대", "text": "적 중대 이상이 고지 A 안에 있음"})
    print("   ref가 점이면 반경 500m, min_echelon은 유닛 환산값(소대 1, 중대 4, 대대 15, 연대 48) 이상을 뜻한다(docs/02 §4).")
    print("시각은 조건이 아니라 일정이다: time_elapsed의 value = D일 00:00부터 경과 시간(h). 'D+1일 06:00' = 30")
    show({"type": "time_elapsed", "value": 6, "text": "D일 06:00"})


def step5():
    h(5, "scenario: 시뮬레이터만 받는 것")
    S = load("data", "cases", CID + ".json")["scenario"]
    print("시작 t=%s, 시뮬레이션 %sh → 끝 t=%s" % (S["start_t"], S["horizon_h"], S["start_t"] + S["horizon_h"]))
    print("\n적의 실제 계획(enemy_plan) — 결과와 무관하게 정해진 계획과 전투력 반응")
    for g in S["enemy_plan"]["groups"]:
        for it in g["items"]:
            when = it.get("start", {}).get("value") if it["timing"] == "계획" else (it.get("trigger") or {}).get("text", "")
            print("   %-4s %-4s %-12s → %-7s %s%s" % (g["group"], it["timing"], it["mode"], it.get("objective_ref"), when,
                                                   "  repeat=%s" % it["repeat"] if it.get("repeat") else ""))
    print("\n숨은 적(hidden_enemy) — 연대가 몰랐던 부대. 생성 모델은 못 보고 시뮬레이터에는 처음부터 있다")
    for e in S["hidden_enemy"]:
        print("   %s %s %s xy=%s" % (e["id"], e["unit"], e["echelon"], e["position"]["xy"]))
    print("\n외생 사건(exogenous) — 전투 결과와 무관한 환경")
    for x in S["exogenous"]:
        print("   t=%-5s %-10s %sh %s" % (x["t"], x["kind"], x.get("duration_h"), x.get("ref", "")))
    print("\n조기 종료(stop_conditions, 하나라도 참이면 끝):")
    for c in S["stop_conditions"]:
        print("   ", c["text"])


def step6():
    h(6, "history: 평가 전용 (시뮬레이터에 주지 않는다)")
    E = eval_view(load("data", "cases", CID + ".json"))
    print("구간 결과:", E["outcome_label"], "| 끝 시각 t =", E["horizon_t"])
    print("끝 시각 실제 상태(outcome_metrics):")
    show(E["history"]["outcome_metrics"], 500)


def step7():
    h(7, "유닛 환산 (sim_unit_table.json)")
    T = load("sim_unit_table.json")
    print("기준:", T["base"])
    for et in ("중대", "대대", "연대"):
        print("   보병 %s = %s" % (et, T["counts"]["infantry"][et]))
    print("   전차 중대 = %s" % T["counts"]["armor"]["중대"])
    print("modifier '+' '-'와 strength_pct 적용 규칙은 docs/02 §3에 있다. 이 표는 보정 대상인 초안이다.")


def step8():
    h(8, "검사: 잘못된 order")
    case = load("data", "cases", CID + ".json")
    good = case["order"]
    print("모범 답안: 오류 %d" % len(validate(case, good)[0]))
    bad = copy.deepcopy(good)
    t = bad["execution"]["tasks"][0]
    t["items"][0]["params"]["objective"] = "HILL_X"                                   # 정의되지 않은 지형 id
    t["items"][1]["trigger"] = {"type": "time_elapsed", "value": 20, "text": "D일 20:00"}  # 즉시 과업에 trigger
    bad["execution"]["concept"]["reserve"]["commit"] = {"type": "time_elapsed", "value": 24, "text": "D+1일 00:00"}  # 시각을 조건으로
    bad["execution"]["tasks"][2]["items"][1]["params"].pop("route")                   # 역습에 route 없음
    err, warn = validate(case, bad)
    print("고친 order: 오류 %d" % len(err))
    for e in err:
        print("   [error]", e)


def step9():
    h(9, "파이프라인")
    from prompt import build_user, GEN_SYSTEM
    s = load("data", "inputs", CID + ".json")
    for cond in ("Z", "D", "F", "DF"):
        u, ex = build_user(s["input"], s["mission_type"], cond, exclude_id=CID)
        print("   조건 %-2s 프롬프트 %6d자  예시 %s" % (cond, len(GEN_SYSTEM) + len(u), ex or "-"))
    print("\n실제 생성:  python3 pipeline/generate_coa.py --case %s --out runs/%s.json --sim-out runs/%s.sim.json" % (CID, CID, CID))
    v = sim_view(load("data", "cases", CID + ".json"))
    print("시뮬레이터 입력(sim_view)의 키:", list(v.keys()), "— order만 새 COA로 바뀐다")


STEPS = [step1, step2, step3, step4, step5, step6, step7, step8, step9]

if __name__ == "__main__":
    pick = [int(a) for a in sys.argv[1:]] or range(1, len(STEPS) + 1)
    for n in pick:
        STEPS[n - 1]()
