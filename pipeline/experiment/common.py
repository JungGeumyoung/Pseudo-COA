"""실험 공통: 경로와 사례 로드. 프롬프트는 pipeline/prompt.py를 그대로 쓴다."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.dirname(HERE)
ROOT = os.path.dirname(PIPE)
sys.path.insert(0, PIPE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from prompt import CONDITIONS, GEN_SYSTEM, IDS, ROW, build_user as _build_user, load, order_schema  # noqa: E402,F401

OUT = os.environ.get("COA_EXP_OUT", os.path.join(HERE, "results"))
HANDOFF = ROOT
COA = PIPE   # backends.py 위치


def case(cid):
    return load(os.path.join(ROOT, "data", "cases", cid + ".json"))


def anon(cid):
    return load(os.path.join(ROOT, "data", "anon", cid + ".json"))


def build_user(cid, cond):
    s = load(os.path.join(ROOT, "data", "inputs", cid + ".json"))
    return _build_user(s["input"], s["mission_type"], cond, exclude_id=cid)[0]


def pick_examples(cid, k=3):
    from prompt import pick_examples as pe
    s = load(os.path.join(ROOT, "data", "inputs", cid + ".json"))
    return pe(s["input"], s["mission_type"], k=k, exclude_id=cid)
