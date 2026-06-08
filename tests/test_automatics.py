"""automatics tests."""

import automatics


def test_stub() -> None:
    """Stub test to ensure the test suite runs."""
    print(automatics.__version__)  # noqa: T201


def test__greet() -> None:
    """Test the greet function."""
    assert automatics.greet("World") == "Hello, World!"


def test__greet_jim() -> None:
    """Test the greet_jim function."""
    assert automatics.greet_jim() == "Hello, Jim!"
