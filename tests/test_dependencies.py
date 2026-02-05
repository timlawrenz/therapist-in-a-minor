import pytest
import importlib

def test_ollama_installed():
    """
    Test that ollama is installed and importable.
    """
    try:
        importlib.import_module("ollama")
    except ImportError:
        pytest.fail("ollama is not installed")
