"""Automatics utility functions."""

import hashlib
import json
from typing import Any

CalculationDict = dict[str, Any]


def hash_from_dict(calc_dct: CalculationDict) -> str:
    """
    Generate hash from calculation dictionary.

    Parameters
    ----------
    calc_dct
        Calculation dictionary.

    Returns
    -------
        Hash string.
    """
    calc_json = json.dumps(
        calc_dct, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(calc_json).hexdigest()
