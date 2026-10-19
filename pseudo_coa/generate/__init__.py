"""COA 생성: 상황 + (교범) + (pseudo-GT 예시) → 생성 모델 → order 블록.

    from pseudo_coa.generate import build_prompt, generate_coa
    system, user, examples = build_prompt("kb2_023", cond="DF")        # 모델 없이 프롬프트만
    order, meta = generate_coa("kb2_023", cond="DF", backend="claude:claude-sonnet-5-5:medium")
"""
from ..data import Case, load_case
from .prompt import CONDITIONS, GEN_SYSTEM, build_user, order_schema  # noqa: F401


def build_prompt(case_or_situation, cond="DF", k=3, mission_type=None):
    """case_or_situation: 사례 id(50건 중 하나, 같은 전투는 예시에서 뺀다) 또는 input 블록 dict(새 상황, mission_type 필요).
    반환: (system, user, 예시 id 목록)."""
    if isinstance(case_or_situation, (str, Case)):
        c = load_case(case_or_situation) if isinstance(case_or_situation, str) else case_or_situation
        situation, mt, exclude = c.situation, mission_type or c.mission_type, c.id
    else:
        situation, mt, exclude = case_or_situation, mission_type, None
        if not mt:
            raise ValueError("새 상황에는 mission_type이 필요하다 (지역방어·기동방어·공격·역습·지연·철수·추격·경계)")
    user, examples = build_user(situation, mt, cond, k=k, exclude_id=exclude)
    return GEN_SYSTEM, user, examples


def generate_coa(case_or_situation, cond="DF", k=3, mission_type=None, backend="claude:claude-sonnet-5-5:medium"):
    """반환: (order 블록, meta). meta에는 고른 예시와 생성 기록이 있다."""
    from .backends import make_backend
    system, user, examples = build_prompt(case_or_situation, cond, k, mission_type)
    be = make_backend(backend) if isinstance(backend, str) else backend
    order, meta = be.generate(system, user, order_schema())
    if "order" in order and "task_organization" not in order:
        order = order["order"]
    meta = dict(meta, cond=cond, examples=examples)
    return order, meta
