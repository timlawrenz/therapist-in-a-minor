import pytest
import importlib

def test_insightface_installed():
    """Test that insightface is installed and importable."""
    try:
        importlib.import_module("insightface")
    except ImportError:
        pytest.fail("insightface is not installed")
