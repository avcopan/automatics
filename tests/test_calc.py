"""Calculation tests."""

import pytest

from automatics import Calculation


@pytest.fixture
def orca_energy() -> Calculation:
    """Sample Calculation fixture."""
    return Calculation(
        program="orca",
        calc_type="energy",
        method="B3LYP",
        basis="6-31G(d)",
        input_data={"foo": "bar"},
    )


def test__hashes(orca_energy: Calculation) -> None:
    """Test Calculation hashing."""
    assert orca_energy.base_hash is not None
    assert orca_energy.full_hash is not None

    assert orca_energy.base_hash != orca_energy.full_hash
