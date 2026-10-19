"""기본 점검: python -m unittest discover tests

- 50건 모두 폴더가 온전하고, 합치면 옛 단일 파일 꼴의 스키마 키를 갖는다
- pseudo-GT 50건이 검사를 통과한다
- 익명판과 실명판의 id·좌표가 같다
- 시뮬레이터 입력에 history가 들어가지 않는다
- 프롬프트에 scenario·history가 새지 않는다 (숨은 적 id가 나오지 않는다)
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pseudo_coa import case_ids, load_case, validate  # noqa: E402
from pseudo_coa.generate import build_prompt  # noqa: E402

FILES = ["situation.json", "coa.json", "scenario.json", "history.json", "source.json", "README.md", "map.svg",
         os.path.join("real_names", "situation.json"), os.path.join("real_names", "coa.json")]


def ids_and_xy(x, out=None):
    out = [] if out is None else out
    if isinstance(x, dict):
        for k, v in sorted(x.items()):
            if k in ("id", "xy", "polygon", "axis_xy", "ref", "group", "objective_ref"):
                out.append((k, json.dumps(v)))
            ids_and_xy(v, out)
    elif isinstance(x, list):
        for v in x:
            ids_and_xy(v, out)
    return out


class TestCases(unittest.TestCase):
    def test_50_cases_complete(self):
        ids = case_ids()
        self.assertEqual(len(ids), 50)
        for i in ids:
            for f in FILES:
                self.assertTrue(os.path.exists(os.path.join(load_case(i).dir, f)), (i, f))
            full = load_case(i).full()
            for k in ("schema", "id", "meta", "input", "order", "scenario", "history", "checks"):
                self.assertIn(k, full, (i, k))

    def test_pseudo_gt_valid(self):
        for i in case_ids():
            err, _ = validate(i, load_case(i).coa)
            self.assertEqual(err, [], i)

    def test_anon_matches_real(self):
        for i in case_ids():
            c = load_case(i)
            self.assertEqual(ids_and_xy(c.situation), ids_and_xy(c.situation_real), i)
            self.assertEqual(ids_and_xy(c.coa), ids_and_xy(c.coa_real), i)

    def test_sim_input_has_no_history(self):
        s = load_case("kb2_023").sim_input()
        self.assertEqual(set(s), {"schema", "id", "scale_m_per_unit", "input", "order", "scenario"})

    def test_prompt_has_no_hidden_enemy(self):
        for i in case_ids():
            hidden = [h["id"] for h in load_case(i).scenario.get("hidden_enemy", [])]
            _, user, _ = build_prompt(i, "DF")
            target = user[user.index("## 이번 과제"):]
            for h in hidden:
                self.assertNotIn('"%s"' % h, target, (i, h))


if __name__ == "__main__":
    unittest.main()
