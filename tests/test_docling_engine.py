import pytest
from pathlib import Path
from extractor.docling_engine import DoclingEngine
from unittest.mock import patch, MagicMock

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
    assert engine.converter is not None

def test_docling_engine_convert():
    engine = DoclingEngine()
    mock_result = MagicMock()
    with patch.object(engine.converter, 'convert', return_value=mock_result) as mock_convert:
        result = engine.convert(Path("test.pdf"))
        mock_convert.assert_called_once_with(Path("test.pdf"))
        assert result == mock_result