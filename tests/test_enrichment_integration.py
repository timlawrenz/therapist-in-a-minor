import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from extractor.cli import cli
import json
import torch

@patch("extractor.enrichment_engine.EnrichmentEngine.extract_faces")
@patch("extractor.enrichment_engine.Image")
@patch("extractor.enrichment_engine.BitImageProcessor")
@patch("extractor.enrichment_engine.Dinov2Model")
@patch("extractor.enrichment_engine.CLIPProcessor")
@patch("extractor.enrichment_engine.CLIPModel")
@patch("ollama.Client")
@patch("extractor.cli.DoclingEngine") # Still mock docling as it's heavy/slow
@patch("extractor.cli.Scanner")
def test_full_pipeline_enrichment(MockScanner, MockDocling, MockOllamaClient, 
                                  MockCLIPModel, MockCLIPProcessor, 
                                  MockDinoModel, MockDinoProcessor, MockImage, MockExtractFaces, tmp_path):
    # Setup
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "test.pdf").touch()
    target_dir = tmp_path / "target"
    
    # Mock Image.open
    mock_image = MockImage.open.return_value
    mock_image.convert.return_value = mock_image
    
    # Mock Scanner
    mock_scanner = MockScanner.return_value
    mock_scanner.scan.return_value = [source_dir / "test.pdf"]
    
    # Mock DoclingEngine to simulate image extraction
    mock_docling_instance = MockDocling.return_value
    images_dir = target_dir / "test" / "images"
    images_dir.mkdir(parents=True)
    img_path = images_dir / "img1.png"
    img_path.write_bytes(b"fake_image_data")
    
    mock_docling_instance.convert.return_value = MagicMock()
    mock_docling_instance.save_images.return_value = [{
        "filename": "img1.png",
        "path": str(img_path)
    }]
    
    # Mock Ollama
    mock_ollama = MockOllamaClient.return_value
    mock_ollama.generate.return_value = {"response": "Mock Description"}
    
    # Mock HF Models (return dummy tensors)
    MockExtractFaces.return_value = [{"bbox": [10, 20, 30, 40], "embedding": [0.9]}]
    # We mock the instance returned by from_pretrained
    mock_dino_model = MockDinoModel.from_pretrained.return_value
    mock_dino_output = MagicMock()
    # DINOv2 output shape is [batch, seq_len, hidden_size]
    # We mocked mean pooling over dim=1
    mock_dino_output.last_hidden_state = torch.tensor([[[0.1]]])
    mock_dino_model.return_value = mock_dino_output
    
    mock_clip_model = MockCLIPModel.from_pretrained.return_value
    # CLIP output shape is [batch, hidden_size]
    mock_clip_model.get_image_features.return_value = torch.tensor([[0.2]])
    
    # Run CLI
    runner = CliRunner()
    result = runner.invoke(cli, ['extract', '--source', str(source_dir), '--target', str(target_dir)])
    
    if result.exit_code != 0:
        print(result.output)
        print(result.exception)
    
    assert result.exit_code == 0
    
    # Verify metadata file
    metadata_file = images_dir / "image_metadata.json"
    assert metadata_file.exists()
    
    with open(metadata_file) as f:
        data = json.load(f)
    
    assert data[0]["description"] == "Mock Description"
    assert data[0]["embeddings"]["dino"] == pytest.approx([0.1])
    assert data[0]["embeddings"]["clip"] == pytest.approx([0.2])
    assert data[0]["faces"][0]["bbox"] == [10, 20, 30, 40]
    assert data[0]["faces"][0]["embedding"] == pytest.approx([0.9])
