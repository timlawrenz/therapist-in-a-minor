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

def test_docling_engine_export(tmp_path):
    engine = DoclingEngine()
    mock_result = MagicMock()
    output_dir = tmp_path
    
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

def test_docling_engine_save_images(tmp_path):
    engine = DoclingEngine()
    mock_result = MagicMock()
    output_dir = tmp_path
    
    # Mock picture item
    mock_pic = MagicMock()
    
    # Mock ImageRef structure
    mock_pil_image = MagicMock()
    
    class MockImageRef:
        def __init__(self, pil):
            self.pil_image = pil
            
    mock_image_ref = MockImageRef(mock_pil_image)
    mock_pic.image = mock_image_ref
    
    # Mock provenance
    mock_pic.prov = [MagicMock(page_no=1)]
    mock_pic.self_ref = "#/pictures/1"
    
    # Mock document.pictures iteration
    mock_result.document.pictures = [mock_pic]
    
    engine.save_images(mock_result, output_dir)
    
    # Verify save was called on the PIL image, not the ImageRef
    mock_pil_image.save.assert_called()

def test_docling_engine_save_images_returns_metadata(tmp_path):
    engine = DoclingEngine()
    mock_result = MagicMock()
    output_dir = tmp_path
    
    mock_pic = MagicMock()
    
    # Mock ImageRef structure
    mock_pil_image = MagicMock()
    class MockImageRef:
        def __init__(self, pil):
            self.pil_image = pil
    
    mock_image_ref = MockImageRef(mock_pil_image)
    mock_pic.image = mock_image_ref

    # Mock provenance
    prov = MagicMock()
    prov.page_no = 1
    # Mock bbox
    mock_bbox = MagicMock()
    mock_bbox.as_tuple.return_value = (0, 0, 100, 100)
    prov.bbox = mock_bbox
    mock_pic.prov = [prov]
    
    mock_result.document.pictures = [mock_pic]
    
    metadata = engine.save_images(mock_result, output_dir)
    
    assert metadata is not None
    assert len(metadata) == 1
    assert metadata[0]["page_no"] == 1
    assert "page_1_img_1.png" in str(metadata[0]["filename"])

def test_docling_engine_manifest(tmp_path):
    engine = DoclingEngine()
    mock_result = MagicMock()
    # Mock pages count
    mock_result.pages = [MagicMock(), MagicMock()]
    
    image_metadata = [{"filename": "img1.png", "page_no": 1}]
    output_path = tmp_path / "manifest.json"
    
    with patch("builtins.open", mock_open()) as mock_file:
        with patch("json.dump") as mock_json_dump:
            engine.generate_manifest(mock_result, output_path, image_metadata)
            
            mock_json_dump.assert_called_once()
            args, _ = mock_json_dump.call_args
            data = args[0]
            
            assert data["page_count"] == 2
            assert data["images"] == image_metadata