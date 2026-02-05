import pytest
from pathlib import Path
from extractor.docling_engine import DoclingEngine
from unittest.mock import patch, MagicMock, mock_open

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

def test_docling_engine_export():

    engine = DoclingEngine()

    mock_result = MagicMock()

    output_dir = Path("tmp_output")

    

    # Mock return values

    mock_result.document.export_to_markdown.return_value = "# Test Markdown"

    mock_result.document.export_to_dict.return_value = {"key": "value"}

    

    # We mock open to avoid writing files

    with patch("builtins.open", mock_open()) as mock_file:

        engine.save_markdown(mock_result, output_dir / "test.md")

        engine.save_json(mock_result, output_dir / "test.json")

        

        # Verify calls

        mock_result.document.export_to_markdown.assert_called_once()

        # Verify file writes (basic check)

        assert mock_file.call_count >= 2
