"""Calculation metadata."""

from typing import Any

from pydantic import BaseModel

CalculationDict = dict[str, Any]


class Model(BaseModel):
    r"""Calculation model specification.

    Attributes
    ----------
    program : str
        Quantum chemistry program used (psi4, ORCA, ...)
    program_version : str, optional
        Quantum chemistry program version.
    calc_type : str
        Calculation type (energy, optimization, ...)
    method : str
        Computational method (B3LYP, MP2, ...)
    basis : str, optional
        Orbital basis set.

    Example
    -------
    ```
    opt_model = Model(
        program = "orca",
        program_version = "6.1.1",
        calc_type = "optimization",
        method = "b3lyp",
        basis = "def2-SVP",
    )
    ```
    """

    program: str
    program_version: str = ""
    calc_type: str
    method: str
    basis: str = ""
