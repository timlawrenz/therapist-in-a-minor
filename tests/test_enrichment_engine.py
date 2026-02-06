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
            "embedding_model_clip": "openai/clip-vit-base-patch32",
            "facial": {
                "enabled": True,
                "device": "cpu",
                "retinaface": {"min_confidence": 0.8},
                "facenet": {"pretrained": "vggface2"},
            },
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


def test_extract_faces_populates_bbox_and_embedding(mock_config, tmp_path):
    from PIL import Image as PILImage

    with patch("extractor.enrichment_engine.load_config", return_value=mock_config):
        engine = EnrichmentEngine()

    image_path = tmp_path / "test_image.png"
    PILImage.new("RGB", (100, 80), color="white").save(image_path)

    with patch.object(engine, "_detect_faces_retinaface", return_value=[[10, 20, 30, 50]]), \
         patch.object(engine, "_embed_faces_facenet", return_value=[[0.1, 0.2, 0.3]]):
        faces = engine.extract_faces(image_path)

    assert len(faces) == 1
    assert faces[0]["bbox"] == [10, 20, 20, 30]
    assert faces[0]["embedding"] == pytest.approx([0.1, 0.2, 0.3])


def test_extract_faces_no_faces_returns_empty(mock_config, tmp_path):
    from PIL import Image as PILImage

    with patch("extractor.enrichment_engine.load_config", return_value=mock_config):
        engine = EnrichmentEngine()

    image_path = tmp_path / "test_image.png"
    PILImage.new("RGB", (100, 80), color="white").save(image_path)

    with patch.object(engine, "_detect_faces_retinaface", return_value=[]):
        faces = engine.extract_faces(image_path)

    assert faces == []


def test_extract_faces_disabled_skips_processing(tmp_path):
    from PIL import Image as PILImage

    config = {
        "enrichment": {
            "facial": {"enabled": False},
        }
    }

    with patch("extractor.enrichment_engine.load_config", return_value=config):
        engine = EnrichmentEngine()

    image_path = tmp_path / "test_image.png"
    PILImage.new("RGB", (10, 10), color="white").save(image_path)

    with patch.object(engine, "_detect_faces_retinaface") as mock_detect:
        faces = engine.extract_faces(image_path)

    assert faces == []
    mock_detect.assert_not_called()
