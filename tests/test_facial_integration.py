import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from click.testing import CliRunner
from extractor.cli import cli

@patch("extractor.cli.FacialEngine")
@patch("extractor.cli.EnrichmentEngine")
@patch("extractor.cli.DoclingEngine")
@patch("extractor.cli.Scanner")
def test_cli_extract_with_facial_enrichment(MockScanner, MockDocling, MockEnrichment, MockFacial, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "doc1.pdf").touch()
    target_dir = tmp_path / "target"
    
    # Mock Scanner
    mock_scanner = MockScanner.return_value
    mock_scanner.scan.return_value = [source_dir / "doc1.pdf"]
    
    # Mock DoclingEngine to simulate image extraction
    mock_docling_instance = MockDocling.return_value
    images_dir = target_dir / "doc1" / "images"
    images_dir.mkdir(parents=True)
    img_path = images_dir / "img1.png"
    img_path.write_bytes(b"fake_image_data")
    
    mock_docling_instance.convert.return_value = MagicMock()
    mock_docling_instance.save_images.return_value = [{
        "filename": "img1.png",
        "path": str(img_path)
    }]
    
    # Mock EnrichmentEngine (image description and DINO/CLIP)
    mock_enrichment_instance = MockEnrichment.return_value
    mock_enrichment_instance.describe_image.return_value = "Image description"
    mock_enrichment_instance.embed_image.return_value = {"dino": [0.1], "clip": [0.2]}
    
    # Mock FacialEngine
    mock_facial_instance = MockFacial.return_value
    mock_facial_instance.enabled = True # Ensure it's enabled for the test
    mock_facial_instance.detect_faces.return_value = [
        {"bbox": [10, 20, 90, 80], "embedding": [0.3, 0.4, 0.5]}
    ]
    
    runner = CliRunner()
    result = runner.invoke(cli, ['extract', '--source', str(source_dir), '--target', str(target_dir)])
    
    assert result.exit_code == 0
    
    # Verify FacialEngine was called
    MockFacial.assert_called_once()
    mock_facial_instance.detect_faces.assert_called_with(img_path)
    
    # Verify metadata.json
    metadata_file = images_dir / "image_metadata.json"
    assert metadata_file.exists()
    
    with open(metadata_file) as f:
        data = json.load(f)
        
    assert len(data) == 1
    assert data[0]["description"] == "Image description"
    assert data[0]["embeddings"]["dino"] == [0.1]
    assert data[0]["embeddings"]["clip"] == [0.2]
    assert "faces" in data[0]
    assert len(data[0]["faces"]) == 1
    assert data[0]["faces"][0]["bbox"] == [10, 20, 90, 80]
    assert data[0]["faces"][0]["embedding"] == [0.3, 0.4, 0.5]

@patch("extractor.cli.FacialEngine")
@patch("extractor.cli.EnrichmentEngine")
@patch("extractor.cli.DoclingEngine")
@patch("extractor.cli.Scanner")
def test_cli_extract_facial_disabled(MockScanner, MockDocling, MockEnrichment, MockFacial, tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "doc1.pdf").touch()
    target_dir = tmp_path / "target"
    
    # Mock Scanner
    mock_scanner = MockScanner.return_value
    mock_scanner.scan.return_value = [source_dir / "doc1.pdf"]
    
    # Mock DoclingEngine to simulate image extraction
    mock_docling_instance = MockDocling.return_value
    images_dir = target_dir / "doc1" / "images"
    images_dir.mkdir(parents=True)
    img_path = images_dir / "img1.png"
    img_path.write_bytes(b"fake_image_data")
    
    mock_docling_instance.convert.return_value = MagicMock()
    mock_docling_instance.save_images.return_value = [{
        "filename": "img1.png",
        "path": str(img_path)
    }]
    
    # Mock EnrichmentEngine (image description and DINO/CLIP)
    mock_enrichment_instance = MockEnrichment.return_value
    mock_enrichment_instance.describe_image.return_value = "Image description"
    mock_enrichment_instance.embed_image.return_value = {"dino": [0.1], "clip": [0.2]}
    
    # Mock FacialEngine - disabled
    mock_facial_instance = MockFacial.return_value
    mock_facial_instance.enabled = False # Ensure it's disabled for the test
    mock_facial_instance.detect_faces.return_value = [] # Should not be called, but good fallback
    
    runner = CliRunner()
    result = runner.invoke(cli, ['extract', '--source', str(source_dir), '--target', str(target_dir)])
    
    assert result.exit_code == 0
    
    # Verify FacialEngine was NOT called (no instance created if disabled)
    MockFacial.assert_called_once() # Still called, but returns an instance with enabled=False
    mock_facial_instance.detect_faces.assert_not_called()
    
    # Verify metadata.json does not contain "faces" key or it's empty
    metadata_file = images_dir / "image_metadata.json"
    assert metadata_file.exists()
    
    with open(metadata_file) as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert "faces" not in data[0] or data[0]["faces"] == []
