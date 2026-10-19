"""사례 파일을 시뮬레이터 입력과 평가 기록으로 나눈다.

    python3 tools/case_io.py sim  data/cases/kb2_023.json                       > sim.json   # 모범 답안 명령으로
    python3 tools/case_io.py sim  data/cases/kb2_023.json --order new_order.json > sim.json   # 새로 생성한 명령으로
    python3 tools/case_io.py eval data/cases/kb2_023.json                       > eval.json
    python3 tools/case_io.py prompt data/cases/kb2_023.json                     > given.json # 생성 모델에 줄 입력(익명화본)

--order 파일은 order 블록 하나({"task_organization": …}) 또는 {"order": {…}} 꼴 모두 받는다.
표준 라이브러리만 쓴다.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_order(path):
    o = load(path)
    return o["order"] if "order" in o and "task_organization" not in o else o


def sim_view(case, order=None):
    """시뮬레이터에 주는 것: input, order, scenario와 축척. history와 meta(결과 요약)는 넣지 않는다."""
    return {
        "schema": case["schema"],
        "id": case["id"],
        "scale_m_per_unit": case["meta"]["geo"]["scale_m_per_unit"],
        "input": case["input"],
        "order": order if order is not None else case["order"],
        "scenario": case["scenario"],
    }


def eval_view(case):
    """평가에만 쓰는 것: 실제 경과와 결과, 구간 결과 라벨."""
    return {
        "id": case["id"],
        "outcome_label": case["meta"]["outcome"]["label"],
        "horizon_t": case["scenario"]["start_t"] + case["scenario"]["horizon_h"],
        "history": case["history"],
    }


def prompt_view(case_path):
    """생성 모델(에이전트)에 주는 것: 익명화된 input. 모범 답안 order는 few-shot 예시로만 쓴다."""
    cid = load(case_path)["id"]
    return load(os.path.join(ROOT, "data", "anon", cid + ".json"))["input"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("view", choices=["sim", "eval", "prompt"])
    ap.add_argument("case")
    ap.add_argument("--order", help="새로 생성한 order JSON")
    a = ap.parse_args()
    case = load(a.case)
    if a.view == "sim":
        out = sim_view(case, load_order(a.order) if a.order else None)
    elif a.view == "eval":
        out = eval_view(case)
    else:
        out = prompt_view(a.case)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
