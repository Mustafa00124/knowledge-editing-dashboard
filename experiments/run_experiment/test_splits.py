"""The dev/test split holds: no leakage, reproducible, matches the data.

Re-derives every record's subject with the runner's own loaders and checks
the split files in splits/ against the leakage rules in
scripts/make_splits.py. Needs the experiment environment and the datasets;
subsets whose data is not downloaded are skipped.
"""
import os
import sys
import unittest
from pathlib import Path

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = Path(EXP_DIR).parents[1]
sys.path.insert(0, str(ROOT / "external" / "EasyEdit"))
sys.path.insert(0, EXP_DIR)
sys.path.insert(0, str(ROOT / "scripts"))

import splits  # noqa: E402


def split_files():
    return sorted((ROOT / "splits").rglob("*.json"))


class SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from eval_utils import load_requests
        from make_splits import group_key

        cls.loaded = {}
        for path in split_files():
            info = splits.load(str(ROOT / splits_data(path)), verify=False)
            data = ROOT / info["data"]
            if data.exists():
                cls.loaded[info["data"]] = (info, [group_key(r) for r in load_requests(str(data), None)])
        cls.held_keys = set()
        for info, keys in cls.loaded.values():
            cls.held_keys |= {keys[i] for i in info["dev"] + info["demo"]}

    def test_split_files_exist_for_every_runnable_subset(self):
        self.assertGreater(len(split_files()), 30)

    def test_data_matches_the_split(self):
        for name, (info, keys) in self.loaded.items():
            with self.subTest(name):
                self.assertEqual(len(keys), info["requests"])
                splits.load(str(ROOT / name))  # raises if the file changed

    def test_parts_are_disjoint_and_sized(self):
        for name, (info, _) in self.loaded.items():
            with self.subTest(name):
                dev, demo, excluded = set(info["dev"]), set(info["demo"]), set(info["excluded"])
                self.assertFalse(dev & demo or dev & excluded or demo & excluded)
                self.assertLessEqual(len(dev), 100)
                test = splits.indices(info, "test")
                self.assertEqual(len(test), info["test_count"])
                self.assertFalse(set(test) & (dev | demo | excluded))
                self.assertGreaterEqual(len(test), info["requests"] // 2)

    def test_no_test_record_shares_a_subject_with_any_dev_or_demo_record(self):
        for name, (info, keys) in self.loaded.items():
            with self.subTest(name):
                leaked = [i for i in splits.indices(info, "test") if keys[i] in self.held_keys]
                self.assertEqual(leaked, [], f"{len(leaked)} test records share a held-out subject")

    def test_a_subject_never_straddles_dev_and_test_within_a_subset(self):
        for name, (info, keys) in self.loaded.items():
            with self.subTest(name):
                dev_keys = {keys[i] for i in info["dev"]}
                test_keys = {keys[i] for i in splits.indices(info, "test")}
                self.assertFalse(dev_keys & test_keys)


def splits_data(split_file):
    # Split files mirror datasets/: splits/<rel> describes datasets/<rel>.
    return Path("datasets") / split_file.relative_to(ROOT / "splits")


if __name__ == "__main__":
    unittest.main()
