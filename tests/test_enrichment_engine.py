import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from extractor.enrichment_engine import EnrichmentEngine
import torch

@pytest.fixture
def mock_config():
    return {
        "enrichment": {
            "ollama_host": "http://localhost:11434",
            "description_model": "llava",
            "embedding_model_dino": "facebook/dinov2-base",
            "embedding_model_clip": "openai/clip-vit-base-patch32"
        }
    }

def test_enrichment_engine_initialization(mock_config):
    """
    Test that the engine initializes with config.
    """
    with patch("extractor.enrichment_engine.load_config", return_value=mock_config):
        engine = EnrichmentEngine()
        assert engine.config == mock_config
        assert engine.ollama_host == "http://localhost:11434"

@patch("ollama.Client")
def test_generate_description(MockClient, mock_config, tmp_path):
    """
    Test generating a text description for an image.
    """
    mock_client_instance = MockClient.return_value
    mock_client_instance.generate.return_value = {"response": "A beautiful test image."}
    
    with patch("extractor.enrichment_engine.load_config", return_value=mock_config):
        engine = EnrichmentEngine()
        image_path = tmp_path / "test_image.png"
        image_path.write_bytes(b"fake_image_data")
        
        description = engine.describe_image(image_path)
        
        assert description == "A beautiful test image."
        mock_client_instance.generate.assert_called_once()

@patch("extractor.enrichment_engine.BitImageProcessor")
@patch("extractor.enrichment_engine.Dinov2Model")
@patch("extractor.enrichment_engine.CLIPProcessor")
@patch("extractor.enrichment_engine.CLIPModel")
@patch("extractor.enrichment_engine.Image")
def test_generate_embeddings_hf(MockImage, MockCLIPModel, MockCLIPProcessor, MockDinoModel, MockDinoProcessor, mock_config, tmp_path):
    """
    Test generating embeddings using HF mocks.
    """
    # Setup DINO mocks
    mock_dino_model = MockDinoModel.from_pretrained.return_value
    mock_dino_output = MagicMock()
    mock_dino_output.last_hidden_state = torch.tensor([[[0.1, 0.2]]]) # [1, 1, 2]
    mock_dino_model.return_value = mock_dino_output
    
    # Setup CLIP mocks
    mock_clip_model = MockCLIPModel.from_pretrained.return_value
    mock_clip_model.get_image_features.return_value = torch.tensor([[0.3, 0.4]])
    
    with patch("extractor.enrichment_engine.load_config", return_value=mock_config):
        engine = EnrichmentEngine()
        image_path = tmp_path / "test_image.png"
        image_path.write_bytes(b"fake_image_data")
        
        embeddings = engine.embed_image(image_path)
        
        assert "dino" in embeddings
        assert "clip" in embeddings
        # Dino output should be mean of [0.1, 0.2] -> [0.1, 0.2]
        assert embeddings["dino"] == pytest.approx([0.1, 0.2])
        assert embeddings["clip"] == pytest.approx([0.3, 0.4])
        
        MockDinoModel.from_pretrained.assert_called_once()
        MockCLIPModel.from_pretrained.assert_called_once()