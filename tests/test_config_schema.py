import os
import yaml
import pytest

CONFIG_PATH = "config.yaml"

def test_config_exists():
    assert os.path.exists(CONFIG_PATH), f"{CONFIG_PATH} does not exist"

def test_config_structure():
    if not os.path.exists(CONFIG_PATH):
        pytest.skip("Config file missing")
    
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    
    assert "docling" in config
    assert "ocr_model" in config["docling"]
    assert "layout_model" in config["docling"]
    assert config["docling"]["ocr_model"] == "https://huggingface.co/zai-org/GLM-OCR"
    assert config["docling"]["layout_model"] == "https://huggingface.co/docling-project/docling-layout-heron-101"
