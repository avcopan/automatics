"""Calculation metadata."""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from ..utils import hash_from_dict

CalculationDict = dict[str, Any]


class Calculation(BaseModel):
    r"""Calculation input parameters and metadata.

    Attributes
    ----------
    program : str
        Quantum chemistry program used (psi4, ORCA, ...)
    calc_type : str
        Calculation type (energy, optimization, ...)
    method : str, optional
        Computational method (B3LYP, MP2, ...)
    basis : str, optional
        Basis set.
    input_data : dict, optional
        Dictionary containing optional calculation parameters.
    provenance_source : str, optional
        Original producer of the provenance data.
    provenance : dict, optional
        Dictionary containing optional provenance data.
    base_hash : str, optional
        Auto-populated attribute hashing base Calculation attributes.
    full_hash : str, optional
        Auto-populated attribute hashing base Calculation attributes and input_data.

    Example
    -------
    ```
    calc = Calculation(
        program = "orca",
        calc_type = "optimization",
        method = "b3lyp",
        basis = "def2-SVP",
        input_data = {
            "inp": "%MAXCORE 4000%\nbase 'opt'\n! B3LYP OPT\n\n*xyzfile 0 2 inp.xyz\n"
        },
        provenance_source = "custom",
        provenance = {
            "program_version": "6.1.1",
            "aux_basis": "def2/J",
            "wall_time": "00:00:05:58",
        }
    )
    ```
    """

    program: str
    calc_type: str
    method: str
    basis: str | None = Field(default=None)
    input_data: dict[str, Any] = Field(default_factory=dict)
    provenance_source: str | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)

    base_hash: str | None = None
    full_hash: str | None = None

    @model_validator(mode="after")
    def populate_hashes(self) -> "Calculation":
        """Automatically compute minimal and full hashes on initialization."""
        base_components = {
            "program": self.program,
            "calc_type": self.calc_type,
            "method": self.method,
            "basis": self.basis,
        }

        if self.base_hash is None:
            self.base_hash = hash_from_dict(base_components)

        if self.full_hash is None:
            full_components = {**base_components, "input_data": self.input_data}
            self.full_hash = hash_from_dict(full_components)

        return self
