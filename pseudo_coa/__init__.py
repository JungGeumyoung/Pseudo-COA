"""Pseudo-COA: 6·25전쟁 연대급 전투 50건의 COA 생성·시뮬레이션 데이터 도구.

    from pseudo_coa import load_case, list_cases, validate
    c = load_case("kb2_023")
    errors, warnings = validate(c, my_order)
    sim = c.sim_input(my_order)

명령줄: python -m pseudo_coa --help
"""
from .data import Case, case_ids, list_cases, load_case  # noqa: F401
from .validate import validate  # noqa: F401

__version__ = "0.6.1"
