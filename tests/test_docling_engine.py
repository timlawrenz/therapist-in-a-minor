import pytest
from extractor.docling_engine import DoclingEngine

def test_docling_engine_initialization():
    engine = DoclingEngine()
    assert engine is not None

def test_docling_engine_config_loading():
    config = {
        "docling": {
            "ocr_model": "https://huggingface.co/zai-org/GLM-OCR",
            "layout_model": "https://huggingface.co/docling-project/docling-layout-heron-101"
        }
    }
    engine = DoclingEngine(config=config)
    assert engine.config["docling"]["ocr_model"] == "https://huggingface.co/zai-org/GLM-OCR"
    
    # Check if converter is initialized with options
    # Note: In docling 2.x, DocumentConverter stores options in its format_converters
    # or we can check the passed options if we mock the converter.
    assert engine.converter is not None
