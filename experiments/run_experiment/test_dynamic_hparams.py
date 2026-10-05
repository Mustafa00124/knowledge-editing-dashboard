"""Every dynamic method's hparams file loads with numbers as numbers: YAML
reads "5e-1" as text, which crashed NMKE (nullspace_threshold), WilKE and
FiDAL (v_lr) on their first runs. FiDAL also carries max_length, which
EasyEdit's evaluator reads."""
import dataclasses
import glob
import os
import sys
import unittest

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, EXP_DIR)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(EXP_DIR)), "external", "EasyEdit"))

from dynamic import fidal, fine, hparams_yaml, nmke, wilke  # noqa: E402

CLASSES = {"NMKE": nmke.NMKEHyperParams, "WilKE": wilke.WilKEHyperParams,
           "FiNE": fine.FiNEHyperParams, "FiDAL": fidal.FiDALHyperParams}


def text_numbers(value, where=""):
    if isinstance(value, str) and hparams_yaml._SCIENTIFIC.match(value.strip()):
        return [where]
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in text_numbers(v, f"{where}.{k}")]
    if isinstance(value, (list, tuple)):
        return [p for i, v in enumerate(value) for p in text_numbers(v, f"{where}[{i}]")]
    return []


class DynamicHparamsTests(unittest.TestCase):
    def test_every_file_loads_numbers_as_numbers(self):
        checked = 0
        for method, cls in CLASSES.items():
            for path in sorted(glob.glob(os.path.join(EXP_DIR, "hparams", method, "*.yaml"))):
                with self.subTest(file=os.path.relpath(path, EXP_DIR)):
                    hp = cls.from_hparams(path)
                    self.assertEqual(text_numbers(dataclasses.asdict(hp)), [])
                    checked += 1
        self.assertGreater(checked, 20)

    def test_the_values_that_crashed(self):
        for path in glob.glob(os.path.join(EXP_DIR, "hparams", "NMKE", "*.yaml")):
            hp = nmke.NMKEHyperParams.from_hparams(path)
            self.assertIsInstance(hp.nullspace_threshold, float)
            self.assertIsInstance(hp.v_lr, float)
        for path in glob.glob(os.path.join(EXP_DIR, "hparams", "WilKE", "*.yaml")):
            self.assertIsInstance(wilke.WilKEHyperParams.from_hparams(path).v_lr, float)
        for path in glob.glob(os.path.join(EXP_DIR, "hparams", "FiDAL", "*.yaml")):
            hp = fidal.FiDALHyperParams.from_hparams(path)
            self.assertIsInstance(hp.base_config["v_lr"], float)
            self.assertEqual(hp.max_length, 40)

    def test_only_scientific_notation_is_converted(self):
        self.assertEqual(hparams_yaml.numbers({"a": "5e-1", "b": "model.layers.{}", "c": ["2E-2", "x1e2"]}),
                         {"a": 0.5, "b": "model.layers.{}", "c": [0.02, "x1e2"]})


if __name__ == "__main__":
    unittest.main()
