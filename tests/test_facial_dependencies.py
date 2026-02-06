import pytest
import importlib

def test_deepface_installed():
    """
    Test that deepface is installed and importable.
    """
    try:
        importlib.import_module("deepface")
    except ImportError:
        pytest.fail("deepface is not installed")
