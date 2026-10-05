"""Reading the dynamic methods' hparams files.

YAML reads scientific notation without a decimal point ("5e-1", "2e-2") as
text, not a number. EasyEdit's own hparams classes convert those back
(HyperParams.construct_float_from_scientific_notation); these methods' own
classes read the yaml themselves, so they do it here. Only values written in
scientific notation are converted, so no other text setting is touched.
"""
import re

import yaml

_SCIENTIFIC = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)[eE][+-]?\d+$")


def numbers(value):
    if isinstance(value, str) and _SCIENTIFIC.match(value.strip()):
        return float(value)
    if isinstance(value, dict):
        return {k: numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [numbers(v) for v in value]
    return value


def load(path):
    with open(path) as f:
        return numbers(yaml.safe_load(f))
