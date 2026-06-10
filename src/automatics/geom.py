"""Molecular geometries."""

import contextlib
import hashlib
from importlib.util import find_spec
from typing import TYPE_CHECKING

import numpy as np
import pint
import py3Dmol
import pyparsing as pp
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pyparsing import pyparsing_common as ppc
from rdkit import Chem
from rdkit.Chem import Mol, rdDetermineBonds

from . import element, rd
from .utils.exceptions import GeometryConversionError, HashGenerationError
from .utils.types import CoordinatesField

_QC_SPEC = find_spec("qcdata")
_QC_AVAILABLE = _QC_SPEC is not None

if _QC_AVAILABLE or TYPE_CHECKING:
    from qcdata import Structure

RADIANS_TO_DEGREES = pint.Quantity("radian").m_as("degree")
DEGREES_TO_RADIANS = 1 / RADIANS_TO_DEGREES


class Geometry(BaseModel):
    """
    Molecular geometry.

    Parameters
    ----------
    symbols
        Atomic symbols in order (e.g., ``["H", "O", "H"]``).
        The length of ``symbols`` must match the number of atoms.
    coordinates
        Cartesian coordinates of the atoms in Angstroms.
        Shape is ``(len(symbols), 3)`` and the ordering corresponds to ``symbols``.
    charge
        Total molecular charge.
    spin
        Number of unpaired electrons, i.e. two times the spin quantum number (``2S``).

    Example
    -------
    ```
    h2o = Geometry(
        symbols = ["H", "O", "H"],
        coordinates = [[0.0, 0.0, -0.74], [0.0, 0.0, 0.0], [0.0, 0.0, 0.74]],
        charge = 0,
        spin = 0,
    )
    ```
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    symbols: list[str]
    coordinates: CoordinatesField
    charge: int | None
    spin: int | None

    hash: str | None = Field(default=None)

    @property
    def masses(self) -> list[float]:
        """Get isotopic masses."""
        return list(map(element.mass, self.symbols))

    @property
    def atomic_numbers(self) -> list[float]:
        """Get atomic numbers."""
        return list(map(element.number, self.symbols))

    @property
    def covalent_radii(self) -> list[float]:
        """Get Pyykko covalent radii in A."""
        return list(map(element.covalent_radius, self.symbols))

    @property
    def nvalences(self) -> list[int]:
        """Get numbers of valence electrons."""
        return list(map(element.nvalence, self.symbols))

    @model_validator(mode="after")
    def populate_hash(self) -> "Geometry":
        """Populate hash immediately after the model is created."""
        # Only populate if hash wasn't explicitly provided
        if self.hash is None:
            with contextlib.suppress(HashGenerationError):
                self.hash = geometry_hash(self, decimals=6)
        return self


# Properties
def geometry_hash(geo: Geometry, decimals: int = 6) -> str:
    """
    Generate geometry hash string.

    Parameters
    ----------
    decimals
        Number of decimal places to round the coordinates before hashing.

    Returns
    -------
        Geometry hash string.
    """
    # Check that all hash fields are present
    if geo.charge is None or geo.spin is None:
        msg = "Geometry charge and spin must be present for hashing."
        raise HashGenerationError(msg, geo)
    # 1. Convert symbols and coordinates to integers
    numbers = geo.atomic_numbers
    icoords = np.rint(geo.coordinates * 10**decimals)
    # 2. Generate bytes representation of each field
    numbers_bytes = np.asarray(numbers, dtype=np.dtype("<i8")).tobytes("C")
    icoords_bytes = icoords.astype(np.dtype("<i8")).tobytes("C")
    charge_bytes = geo.charge.to_bytes(1, byteorder="little", signed=True)
    spin_bytes = geo.spin.to_bytes(1, byteorder="little", signed=True)
    # 3. Combine all bytes and generate hash
    geo_bytes = b"|".join([numbers_bytes, icoords_bytes, charge_bytes, spin_bytes])
    return hashlib.sha256(geo_bytes).hexdigest()


# Visualization
def view(
    geo: Geometry, *, view: py3Dmol.view | None = None, label: bool = False
) -> py3Dmol.view:
    """View a geometry with py3Dmol.

    Parameters
    ----------
    geo
        Geometry.
    view
        py3Dmol view.
    label
        Whether to add atom labels to the view.

    Returns
    -------
        py3Dmol view.
    """
    view = py3Dmol.view(width=400, height=400) if view is None else view
    xyz_str = xyz_block(geo)
    view.addModel(xyz_str, "xyz")
    view.setStyle({"stick": {}, "sphere": {"scale": 0.3}})
    if label:
        for key in range(len(geo.symbols)):
            view.addLabel(
                key,
                {
                    "backgroundOpacity": 0.0,
                    "fontColor": "black",
                    "alignment": "center",
                    "inFront": True,
                },
                {"index": key},
            )
    return view


def rdkit_mol(geo: Geometry) -> Mol:
    """
    Instantiate an rdkit Mol from a Geometry.

    Parameters
    ----------
    geo
        Geometry object.

    Returns
    -------
    Mol
        rdkit Mol instance.
    """
    if geo.charge != 0:
        msg = "Determining bond connectivity with charges not implemented."
        raise GeometryConversionError(msg)

    if geo.spin is None:
        msg = "Cannot determine bond connectivity without an assigned value for spin."
        raise GeometryConversionError(msg)

    raw_mol = Chem.MolFromXYZBlock(xyz_block(geo))
    conn_mol = Chem.Mol(raw_mol)
    rdDetermineBonds.DetermineBonds(conn_mol, charge=-geo.spin)

    for a in conn_mol.GetAtoms():
        charge = a.GetFormalCharge()
        a.SetNumRadicalElectrons(abs(charge))
        a.SetFormalCharge(0)

    return conn_mol


def from_rdkit_mol(mol: Mol) -> Geometry:
    """
    Instantiate a Geometry from an rdkit molecule.

    Parameters
    ----------
    mol
        `rdkit.Chem.Mol` instance

    Returns
    -------
        `Geometry` instance.
    """
    if not rd.mol.has_coordinates(mol):
        mol = rd.mol.add_coordinates(mol)

    return Geometry(
        symbols=rd.mol.symbols(mol),
        coordinates=rd.mol.coordinates(mol),
        charge=rd.mol.charge(mol),
        spin=rd.mol.spin(mol),
    )


def xyz_block(geo: Geometry) -> str:
    """
    Return geometry as formatted xyz block.

    Parameters
    ----------
    geo
        Geometry object.

    Returns
    -------
    xyz
        Formatted xyz block.
    """
    lines = [f"{len(geo.symbols)}", ""]
    for sym, (x, y, z) in zip(geo.symbols, geo.coordinates, strict=True):
        lines.append(f"{sym:<2} {x:12.8f} {y:12.8f} {z:12.8f}")

    return "\n".join(lines)


CHAR = pp.Char(pp.alphas)
SYMBOL = pp.Combine(CHAR + pp.Opt(CHAR))
XYZ_LINE = SYMBOL + pp.Group(ppc.fnumber * 3) + pp.Suppress(... + pp.LineEnd())


def from_xyz_block(
    xyz_str: str, *, charge: int | None = None, spin: int | None = None
) -> Geometry:
    """
    Instantiate Geometry from formatted xyz block.

    Parameters
    ----------
    geo_str
        Formatted xyz block.
    charge
        Total molecular charge.
    spin
        Number of unpaired electrons, i.e. two times the spin quantum number (``2S``).

    Returns
    -------
    Geometry
        Geometry object.
    """
    xyz_str = xyz_str.strip()
    lines = xyz_str.splitlines()[2:]
    if not lines:
        msg = "Could not read lines from provided xyz string."
        raise GeometryConversionError(msg)

    symbs, coords = zip(
        *[XYZ_LINE.parse_string(line).as_list() for line in lines], strict=True
    )
    return Geometry(
        symbols=list(symbs), coordinates=np.array(coords), charge=charge, spin=spin
    )


def qc_structure(geo: Geometry) -> Structure:
    """Instantiate a qc Structure from a Geometry."""
    if not _QC_AVAILABLE:
        msg = "qcdata module is not available for Structure conversion."
        raise GeometryConversionError(msg)

    if geo.spin is None:
        msg = "Conversion to Structure with `spin = None` is not supported."
        raise GeometryConversionError(msg)

    return Structure(
        symbols=geo.symbols,
        geometry=np.array(geo.coordinates) * pint.Quantity("angstrom").m_as("bohr"),
        charge=geo.charge,
        multiplicity=geo.spin + 1,
    )


def to_qc_structure(struc: Structure) -> Geometry:
    """Instantiate Geometry from qc Structure."""
    if not _QC_AVAILABLE:
        msg = "qcdata module is not available for Structure conversion."
        raise GeometryConversionError(msg)

    return Geometry(
        symbols=struc.symbols,
        coordinates=struc.geometry * pint.Quantity("bohr").m_as("angstrom"),
        charge=struc.charge,
        spin=struc.multiplicity - 1,
    )
