import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from extractor.facial_engine import FacialEngine
import numpy as np

@pytest.fixture
def mock_config():
    return {
        "enrichment": {
            "facial": {
                "enabled": True,
                "model_name": "buffalo_l",
                "det_thresh": 0.5
            }
        }
    }

@patch("extractor.facial_engine.FaceAnalysis")
def test_facial_engine_initialization(MockFaceAnalysis, mock_config):
    with patch("extractor.facial_engine.load_config", return_value=mock_config):
        engine = FacialEngine()
        assert engine.config == mock_config
        # We expect it to be initialized with the model name from config
        MockFaceAnalysis.assert_called_with(name="buffalo_l")
        engine.app.prepare.assert_called()

@patch("extractor.facial_engine.FaceAnalysis")
@patch("extractor.facial_engine.cv2")
def test_detect_faces(MockCV2, MockFaceAnalysis, mock_config, tmp_path):
    mock_app = MockFaceAnalysis.return_value
    
    # Mock face object returned by insightface
    mock_face = MagicMock()
    # InsightFace bbox is [x1, y1, x2, y2]. Spec asked for [x, y, w, h].
    # Let's say x1=10, y1=20, x2=100, y2=100. Width=90, Height=80.
    mock_face.bbox = np.array([10, 20, 100, 100]) 
    mock_face.embedding = np.array([0.1, 0.2, 0.3])
    
    mock_app.get.return_value = [mock_face]
    
    # Mock image reading
    MockCV2.imread.return_value = np.zeros((200, 200, 3), dtype=np.uint8)
    
    with patch("extractor.facial_engine.load_config", return_value=mock_config):
        engine = FacialEngine()
        image_path = tmp_path / "test.png"
        image_path.touch()
        
        faces = engine.detect_faces(image_path)
        
        assert len(faces) == 1
        # Check conversion to [x, y, w, h]
        # x=10, y=20, w=100-10=90, h=100-20=80
        assert faces[0]["bbox"] == [10, 20, 90, 80]
        # Check embedding is list, not numpy array
        assert faces[0]["embedding"] == [0.1, 0.2, 0.3]
        
        MockCV2.imread.assert_called_with(str(image_path))
        mock_app.get.assert_called()

@patch("extractor.facial_engine.FaceAnalysis")
def test_detect_faces_disabled(MockFaceAnalysis, mock_config, tmp_path):
    mock_config["enrichment"]["facial"]["enabled"] = False
    
    with patch("extractor.facial_engine.load_config", return_value=mock_config):
        engine = FacialEngine()
        # Should not initialize app if disabled
        MockFaceAnalysis.assert_not_called()
        
        image_path = tmp_path / "test.png"
        faces = engine.detect_faces(image_path)
        assert faces == []
