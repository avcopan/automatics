"""Geometry tests."""

import numpy as np
import pytest
from rdkit.Chem import Mol

from automatics import Geometry, convert_from, geom
from automatics.models.geom import GeometryConversionError, HashGenerationError


@pytest.fixture
def water() -> Geometry:
    """Water geometry fixture."""
    return Geometry(
        symbols=["O", "H", "H"],
        coordinates=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        charge=0,
        spin=0,
    )


def test__hash(water: Geometry) -> None:
    """Test geometry hashing."""
    exp_hash = "67eecf41909c735495d035b556a1adf51f9fb9e1c5a6219be36a2b31a2dd3fa4"
    assert geom.geometry_hash(water) == exp_hash


def test__unhashable() -> None:
    """Test that geometry hashing raises exception without necessary fields."""
    geo = Geometry(
        symbols=["H"], coordinates=np.array([[0, 0, 0]]), charge=None, spin=None
    )
    with pytest.raises(HashGenerationError):
        geom.geometry_hash(geo)


def test__deterministic_hash(water: Geometry) -> None:
    """Test deterministic geometry hashing."""
    water2 = Geometry(
        symbols=["O", "H", "H"],
        coordinates=np.array([[0, 0, 0], [1, 0, 0], [0, 1.000000000000001, 0]]),
        charge=0,
        spin=0,
    )
    assert geom.geometry_hash(water) == geom.geometry_hash(water2)


def test__rdkit_roundtrip(water: Geometry) -> None:
    """Test Geometry to mol roundtrip."""
    mol = convert_from(water, target_type=Mol)
    geo_rt = convert_from(mol, target_type=Geometry)

    assert water.hash == geo_rt.hash


def test__string_roundtrip(water: Geometry) -> None:
    """Test Geometry to xyz string roundtrip."""
    xyz = convert_from(water, target_type=str)
    geo_rt = convert_from(xyz, target_type=Geometry)

    assert water.symbols == geo_rt.symbols
    assert np.allclose(water.coordinates, geo_rt.coordinates)


def test__qc_unavailable(water: Geometry) -> None:
    """Test qcdata is unavailable in base package."""
    assert geom.qc_structure.__module__
    with pytest.raises(GeometryConversionError):
        geom.qc_structure(water)
