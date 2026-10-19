"""실험 공통: 사례 로드와 프롬프트. 모두 pseudo_coa 패키지를 그대로 쓴다(실험 당시 프롬프트와 글자 단위로 같음)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from pseudo_coa import load_case  # noqa: E402
from pseudo_coa.data import read_json as load  # noqa: E402,F401
from pseudo_coa.generate import build_prompt  # noqa: E402
from pseudo_coa.generate.prompt import CONDITIONS, GEN_SYSTEM, IDS, ROW, order_schema  # noqa: E402,F401

OUT = os.environ.get("COA_EXP_OUT", os.path.join(HERE, "results"))


def case(cid):
    """옛 단일 파일 꼴(실명판) 사례. 채점은 id·좌표만 보므로 실명·익명과 무관하다."""
    return load_case(cid).full()


def pseudo_gt(cid):
    c = load_case(cid)
    return {"input": c.situation, "order": c.coa}


def build_user(cid, cond):
    return build_prompt(cid, cond)[1]


def pick_examples(cid, k=3):
    return build_prompt(cid, "F", k)[2]
