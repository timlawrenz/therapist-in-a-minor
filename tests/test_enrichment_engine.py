import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from extractor.enrichment_engine import EnrichmentEngine

@pytest.fixture
def mock_config():
    return {
        "enrichment": {
            "ollama_host": "http://localhost:11434",
            "description_model": "llava",
            "embedding_model_dino": "dinov2",
            "embedding_model_clip": "clip"
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
        args, kwargs = mock_client_instance.generate.call_args
        assert kwargs["model"] == "llava"
        assert "images" in kwargs

@patch("ollama.Client")
def test_generate_embeddings(MockClient, mock_config, tmp_path):
    """
    Test generating embeddings for an image.
    """
    mock_client_instance = MockClient.return_value
    # Ollama embedding response format
    mock_client_instance.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}
    
    with patch("extractor.enrichment_engine.load_config", return_value=mock_config):
        engine = EnrichmentEngine()
        image_path = tmp_path / "test_image.png"
        image_path.write_bytes(b"fake_image_data")
        
        embeddings = engine.embed_image(image_path)
        
        assert "dino" in embeddings
        assert "clip" in embeddings
        assert embeddings["dino"] == [0.1, 0.2, 0.3]
        assert embeddings["clip"] == [0.1, 0.2, 0.3]
        assert mock_client_instance.embeddings.call_count == 2
