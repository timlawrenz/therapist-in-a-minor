import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import cv2

# InsightFace
from insightface.app import FaceAnalysis

from .utils import load_config

logger = logging.getLogger(__name__)

class FacialEngine:
    """
    Handles facial detection and embedding using InsightFace.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        facial_config = self.config.get("enrichment", {}).get("facial", {})
        
        self.enabled = facial_config.get("enabled", False)
        if not self.enabled:
            logger.info("Facial enrichment is disabled.")
            self.app = None
            return
            
        self.model_name = facial_config.get("model_name", "buffalo_l")
        self.det_thresh = facial_config.get("det_thresh", 0.5)
        
        try:
            logger.info("Initializing InsightFace... This may take a few minutes to download models on the first run.")
            self.app = FaceAnalysis(name=self.model_name)
            self.app.prepare(ctx_id=-1, det_thresh=self.det_thresh) # ctx_id=0 for GPU, -1 for CPU
            logger.info(f"InsightFace model '{self.model_name}' loaded successfully (forced CPU).")
        except Exception as e:
            logger.error(f"Failed to load InsightFace model '{self.model_name}': {e}")
            self.app = None
            self.enabled = False

    def detect_faces(self, image_path: Path) -> List[Dict[str, Any]]:
        """
        Detects faces in an image and generates embeddings.
        Returns a list of dictionaries, each with 'bbox' and 'embedding'.
        """
        if not self.enabled or not self.app:
            return []

        image_path = Path(image_path)
        if not image_path.exists():
            logger.warning(f"Image not found for facial detection: {image_path}")
            return []

        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"Could not read image for facial detection: {image_path}")
                return []

            faces = self.app.get(img)
            
            detected_faces = []
            for face in faces:
                # bbox is [x1, y1, x2, y2]. Convert to [x, y, w, h]
                bbox = face.bbox.astype(int).tolist()
                x, y, x2, y2 = bbox
                w, h = x2 - x, y2 - y
                
                detected_faces.append({
                    "bbox": [x, y, w, h],
                    "embedding": face.embedding.tolist() # Convert numpy array to list
                })
            return detected_faces
        except Exception as e:
            logger.error(f"Error during facial detection for {image_path}: {e}")
            return []
