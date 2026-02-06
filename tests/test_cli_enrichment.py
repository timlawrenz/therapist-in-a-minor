import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from click.testing import CliRunner
from extractor.cli import cli

@patch("extractor.cli.EnrichmentEngine")
@patch("extractor.cli.DoclingEngine")
@patch("extractor.cli.Scanner")
def test_extract_command_invokes_enrichment(MockScanner, MockDoclingEngine, MockEnrichmentEngine, tmp_path):
    # Setup
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "test.pdf").touch()
    target_dir = tmp_path / "target"
    
    # Mock Scanner
    mock_scanner = MockScanner.return_value
    mock_scanner.scan.return_value = [source_dir / "test.pdf"]
    
    # Mock DoclingEngine
    mock_docling = MockDoclingEngine.return_value
    mock_docling.convert.return_value = MagicMock()
    
    # Ensure directory exists for metadata writing
    images_dir = target_dir / "test" / "images"
    images_dir.mkdir(parents=True)
    
    # Return one image in metadata
    image_metadata = [{
        "filename": "img1.png",
        "path": str(images_dir / "img1.png")
    }]
    mock_docling.save_images.return_value = image_metadata
    
    # Mock EnrichmentEngine
    mock_enrichment = MockEnrichmentEngine.return_value
    mock_enrichment.describe_image.return_value = "A description"
    mock_enrichment.embed_image.return_value = {"dino": [0.1], "clip": [0.2]}
    mock_enrichment.extract_faces.return_value = [{"bbox": [1, 2, 3, 4], "embedding": [0.5, 0.6]}]
    
    runner = CliRunner()
    result = runner.invoke(cli, ['extract', '--source', str(source_dir), '--target', str(target_dir)])
    
    assert result.exit_code == 0
    
    # Verify EnrichmentEngine was initialized and called
    MockEnrichmentEngine.assert_called_once()
    mock_enrichment.describe_image.assert_called()
    mock_enrichment.embed_image.assert_called()
    
    # Verify arguments
    args, _ = mock_enrichment.describe_image.call_args
    assert str(args[0]) == str(target_dir / "test" / "images" / "img1.png")
    
    # Verify metadata file created
    import json
    metadata_file = target_dir / "test" / "images" / "image_metadata.json"
    assert metadata_file.exists()
    with open(metadata_file) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["description"] == "A description"
    assert data[0]["embeddings"]["dino"] == [0.1]
    assert data[0]["faces"][0]["bbox"] == [1, 2, 3, 4]
    assert data[0]["faces"][0]["embedding"] == [0.5, 0.6]
