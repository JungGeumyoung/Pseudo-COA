"""사례 읽기. 사례 하나는 cases/<id>/ 폴더 하나다.

    from pseudo_coa import load_case, list_cases
    c = load_case("kb2_023")
    c.situation      # 상황(input 블록, 익명화)   — 생성 모델에 준다
    c.coa            # pseudo-GT COA(order 블록, 익명화) — few-shot 예시
    c.scenario       # 적 계획·환경 — 시뮬레이터만
    c.history        # 실제 경과 — 평가만
    c.meta           # 출처, 결과 라벨, 축척
    c.sim_input(my_order)   # 시뮬레이터에 넣을 JSON (order만 바꿔 끼운다)
    c.eval_target()         # 평가 기준
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(ROOT, "cases")
SCHEMA_DIR = os.path.join(ROOT, "schema")
DOCTRINE_DIR = os.path.join(ROOT, "doctrine")


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_cases(**filters):
    """cases/cases.csv의 행 목록. 예: list_cases(mission_type="지역방어", calibration_ok="true")"""
    with open(os.path.join(CASES_DIR, "cases.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if all(r.get(k) == str(v) for k, v in filters.items())]


def case_ids(**filters):
    return [r["id"] for r in list_cases(**filters)]


def order_block(x):
    """{"order": {...}} 꼴이든 order 블록 자체든 order 블록을 돌려준다."""
    return x["order"] if isinstance(x, dict) and "order" in x and "task_organization" not in x else x


class Case(object):
    def __init__(self, case_id):
        self.id = case_id
        self.dir = os.path.join(CASES_DIR, case_id)
        if not os.path.isdir(self.dir):
            raise KeyError("사례 없음: %s (cases/cases.csv 참고)" % case_id)
        self._cache = {}

    def _part(self, name, key):
        if name not in self._cache:
            self._cache[name] = read_json(os.path.join(self.dir, name))
        return self._cache[name][key] if key else self._cache[name]

    # 파일 하나 = 블록 하나
    situation = property(lambda self: self._part("situation.json", "input"))
    mission_type = property(lambda self: self._part("situation.json", "mission_type"))
    coa = property(lambda self: self._part("coa.json", "order"))
    scenario = property(lambda self: self._part("scenario.json", "scenario"))
    history = property(lambda self: self._part("history.json", "history"))
    source = property(lambda self: self._part("source.json", None))
    meta = property(lambda self: self._part("source.json", "meta"))
    checks = property(lambda self: self._part("source.json", "checks"))
    schema = property(lambda self: self._part("source.json", "schema"))
    situation_real = property(lambda self: self._part(os.path.join("real_names", "situation.json"), "input"))
    coa_real = property(lambda self: self._part(os.path.join("real_names", "coa.json"), "order"))

    @property
    def title(self):
        return self.meta["title"]

    @property
    def scale_m_per_unit(self):
        return self.meta["geo"]["scale_m_per_unit"]

    def full(self, real_names=True):
        """옛 단일 파일 꼴 {meta, input, order, scenario, history, checks, …}. real_names=True면 원본(실명)과 같다."""
        d = dict(self.source)
        d.update(input=self.situation_real if real_names else self.situation,
                 order=self.coa_real if real_names else self.coa,
                 scenario=self.scenario, history=self.history)
        return d

    def sim_input(self, order=None):
        """시뮬레이터 입력: 상황 + COA + 시나리오 + 축척. order를 주면 pseudo-GT 대신 그 COA를 넣는다. history는 넣지 않는다."""
        return {"schema": self.schema, "id": self.id, "scale_m_per_unit": self.scale_m_per_unit,
                "input": self.situation, "order": order_block(order) if order is not None else self.coa,
                "scenario": self.scenario}

    def eval_target(self):
        """평가 기준: 구간 결과 라벨, 끝 시각, 실제 경과. 시뮬레이션이 끝난 뒤에만 연다."""
        return {"id": self.id, "outcome_label": self.meta["outcome"]["label"],
                "horizon_t": self.scenario["start_t"] + self.scenario["horizon_h"], "history": self.history}

    def __repr__(self):
        return "<Case %s %s (%s)>" % (self.id, self.title, self.mission_type)


def load_case(case_id):
    return Case(case_id)
