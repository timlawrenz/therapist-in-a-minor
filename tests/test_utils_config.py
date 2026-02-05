import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from extractor.utils import load_config

def test_load_config_success():
    mock_yaml = """
    docling:
      ocr_model: "test_ocr_model"
      layout_model: "test_layout_model"
    """
    with patch("builtins.open", mock_open(read_data=mock_yaml)):
        with patch("pathlib.Path.exists", return_value=True):
            config = load_config("dummy_config.yaml")
            assert config["docling"]["ocr_model"] == "test_ocr_model"
            assert config["docling"]["layout_model"] == "test_layout_model"

def test_load_config_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            load_config("non_existent.yaml")
