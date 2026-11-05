"""Two-level factorial designs and their effects analysis (factorial.py)."""
import itertools
import math
import random
import unittest

import factorial


def columns(rows):
    return list(zip(*rows))


class DesignTests(unittest.TestCase):
    def test_published_fractions_have_their_resolution(self):
        claimed = {(6, 2): 4, (7, 2): 4, (8, 2): 5, (8, 3): 4, (9, 2): 6, (9, 3): 4, (10, 2): 6,
                   (10, 3): 5, (10, 4): 4, (11, 4): 5}
        self.assertEqual(set(claimed), set(factorial.GENERATORS))
        for (k, p), res in claimed.items():
            self.assertEqual(factorial.resolution(k, p), res, (k, p))
        for k in range(3, 12):
            self.assertEqual(factorial.resolution(k, 1), k)
            self.assertIsNone(factorial.resolution(k, 0))

    def test_every_design_is_balanced_and_its_main_effects_orthogonal(self):
        for k in range(2, 12):
            for option in factorial.fractions(k):
                if option["runs"] > 1024:
                    continue
                rows = factorial.design(k, option["p"])
                self.assertEqual(len(rows), option["runs"])
                self.assertEqual(len({tuple(r) for r in rows}), len(rows), "no corner twice")
                cols = columns(rows)
                for col in cols:
                    self.assertEqual(sum(col), 0, (k, option["p"]))
                for a, b in itertools.combinations(cols, 2):
                    self.assertEqual(sum(x * y for x, y in zip(a, b)), 0, (k, option["p"]))

    def test_resolution_v_keeps_every_main_effect_and_pair_apart(self):
        # Every main-effect and two-factor-interaction column is orthogonal to
        # every other one, so none is aliased with another.
        for k, p in ((8, 2), (9, 2), (10, 3), (7, 1)):
            rows = factorial.design(k, p)
            terms = [(i,) for i in range(k)] + list(itertools.combinations(range(k), 2))
            cols = [[math.prod(r[i] for i in t) for r in rows] for t in terms]
            for a, b in itertools.combinations(cols, 2):
                self.assertEqual(sum(x * y for x, y in zip(a, b)), 0, (k, p))

    def test_default_fraction_is_full_up_to_six_settings_then_resolution_v(self):
        runs = {k: 2 ** (k - factorial.default_fraction(k)) for k in range(2, 12)}
        self.assertEqual(runs[5], 32)
        self.assertEqual(runs[6], 64)
        self.assertEqual(runs[7], 64)    # 2^(7-1) VII
        self.assertEqual(runs[8], 64)    # 2^(8-2) V
        self.assertEqual(runs[9], 128)   # 2^(9-2) VI
        self.assertEqual(runs[10], 128)  # 2^(10-3) V
        self.assertEqual(runs[11], 128)  # 2^(11-4) V
        # 64 runs stays on offer for 9 and 10 settings, at resolution IV.
        for k in (9, 10):
            sixty_four = [o for o in factorial.fractions(k) if o["runs"] == 64]
            self.assertEqual([o["resolution"] for o in sixty_four], [4])

    def test_unknown_fractions_are_refused(self):
        with self.assertRaises(ValueError):
            factorial.design(5, 2)  # only resolution III exists
        with self.assertRaises(ValueError):
            factorial.design(12, 0)


class CentreTests(unittest.TestCase):
    def test_middle_values(self):
        self.assertEqual(factorial.centre_value(1.5e-4, 1.5e-3, "log"), (0.000474, False))
        self.assertEqual(factorial.centre_value(12, 50, "int"), (24, False))
        self.assertEqual(factorial.centre_value(0, 0.01, "choice"), (0.005, False))
        self.assertEqual(factorial.centre_value(0.7, 0.99, "choice"), (0.845, False))
        self.assertEqual(factorial.centre_value([3], [7], "layer"), ([5], False))
        self.assertEqual(factorial.centre_value(list(range(0, 18)), list(range(18, 36)), "layer_span"),
                         (list(range(9, 27)), False))
        self.assertEqual(factorial.centre_value([2, 3, 4, 5, 6], [6, 7, 8, 9, 10], "layer_window"),
                         ([4, 5, 6, 7, 8], False))
        self.assertEqual(factorial.centre_value(["q_proj", "v_proj"], ["up_proj"], "choice"), (["q_proj", "v_proj"], True))
        self.assertEqual(factorial.centre_value("implication", "all", "choice"), ("implication", True))

    def test_run_codes(self):
        self.assertEqual(factorial.code_label({"a": 1, "b": -1, "c": 0}, ["a", "b", "c"]), "HLM")


class AnalysisTests(unittest.TestCase):
    def test_t_quantiles(self):
        self.assertAlmostEqual(factorial.t_quantile(0.975, 2), 4.303, places=3)
        self.assertAlmostEqual(factorial.t_quantile(0.975, 10), 2.228, places=3)
        self.assertAlmostEqual(factorial.t_quantile(0.5, 5), 0.0, places=6)

    def test_lenth_finds_the_real_effects_and_not_the_noise(self):
        factors = ["a", "b", "c", "d", "e", "f", "g", "h"]
        rows = factorial.design(8, 2)
        rng = random.Random(1)
        corners = []
        for row in rows:
            x = dict(zip(factors, row))
            y = 0.5 + 0.2 * x["a"] - 0.15 * x["c"] + 0.1 * x["a"] * x["b"] + rng.gauss(0, 0.01)
            corners.append({"coded": x, "y": y})
        result = factorial.analyse(factors, corners, [], "y")
        self.assertTrue(result["complete"])
        main = {m["factor"]: m for m in result["main"]}
        self.assertAlmostEqual(main["a"]["effect"], 0.4, delta=0.02)
        self.assertAlmostEqual(main["c"]["effect"], -0.3, delta=0.02)
        self.assertEqual(main["a"]["verdict"], "strong")
        self.assertEqual(main["c"]["verdict"], "strong")
        self.assertEqual({m["verdict"] for f, m in main.items() if f not in ("a", "c")}, {"noise"})
        top = result["interactions"][0]
        self.assertEqual(top["factors"], ["a", "b"])
        self.assertAlmostEqual(top["effect"], 0.2, delta=0.02)
        self.assertEqual(top["aliases"], [], "resolution V: no pair shares its column")
        self.assertEqual(len(result["interactions"]), 28)

    def test_resolution_iv_names_the_aliased_pairs(self):
        factors = list("abcdefghj")
        rows = factorial.design(9, 3)
        corners = [{"coded": dict(zip(factors, r)), "y": float(r[0])} for r in rows]
        result = factorial.analyse(factors, corners, [], "y")
        self.assertTrue(any(i["aliases"] for i in result["interactions"]))
        self.assertLess(len(result["interactions"]), 36)

    def test_missing_runs_are_left_out_not_zero(self):
        factors = ["a", "b", "c"]
        corners = [{"coded": dict(zip(factors, r)), "y": 1.0 if r[0] > 0 else 0.0} for r in factorial.design(3, 0)]
        corners[1]["y"] = None
        result = factorial.analyse(factors, corners, [], "y")
        self.assertFalse(result["complete"])
        self.assertEqual(result["used"], 7)
        self.assertEqual({m["factor"]: m["effect"] for m in result["main"]}["a"], 1.0)

    def test_curvature_from_the_centre_runs(self):
        bent = factorial.curvature([0.2, 0.3, 0.2, 0.3], [0.8, 0.82, 0.79])
        self.assertAlmostEqual(bent["difference"], 0.553, places=3)
        self.assertTrue(bent["significant"])
        flat = factorial.curvature([0.2, 0.3, 0.2, 0.3], [0.2, 0.3, 0.25])
        self.assertFalse(flat["significant"])
        self.assertIsNone(factorial.curvature([0.2], [0.3])["significant"])


if __name__ == "__main__":
    unittest.main()
