import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import ollama
from PIL import Image
import torch
from transformers import AutoImageProcessor, AutoModel, CLIPProcessor, CLIPModel, BitImageProcessor, Dinov2Model

from .utils import load_config

logger = logging.getLogger(__name__)

class EnrichmentEngine:
    """
    Handles image enrichment (descriptions and embeddings).
    - Descriptions via Ollama (local LLM).
    - Embeddings via Hugging Face Transformers (local execution).
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        enrichment_config = self.config.get("enrichment", {})
        
        self.ollama_host = enrichment_config.get("ollama_host", "http://localhost:11434")
        self.description_model = enrichment_config.get("description_model", "llava")
        
        # Model IDs for HF
        self.embedding_model_dino_id = enrichment_config.get("embedding_model_dino", "facebook/dinov2-base")
        self.embedding_model_clip_id = enrichment_config.get("embedding_model_clip", "openai/clip-vit-base-patch32")
        
        # Initialize Ollama client
        self.client = ollama.Client(host=self.ollama_host)
        
        # Lazy loading for HF models
        self._dino_processor = None
        self._dino_model = None
        self._clip_processor = None
        self._clip_model = None

    def _get_dino(self):
        if not self._dino_model:
            try:
                logger.info(f"Loading DINOv2 model: {self.embedding_model_dino_id}")
                self._dino_processor = BitImageProcessor.from_pretrained(self.embedding_model_dino_id)
                self._dino_model = Dinov2Model.from_pretrained(self.embedding_model_dino_id)
                self._dino_model.eval()
            except Exception as e:
                logger.error(f"Failed to load DINOv2 model: {e}")
        return self._dino_processor, self._dino_model

    def _get_clip(self):
        if not self._clip_model:
            try:
                logger.info(f"Loading CLIP model: {self.embedding_model_clip_id}")
                self._clip_processor = CLIPProcessor.from_pretrained(self.embedding_model_clip_id)
                self._clip_model = CLIPModel.from_pretrained(self.embedding_model_clip_id)
                self._clip_model.eval()
            except Exception as e:
                logger.error(f"Failed to load CLIP model: {e}")
        return self._clip_processor, self._clip_model

    def describe_image(self, image_path: Path) -> str:
        """
        Generates a natural language description of an image using Ollama.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            logger.warning(f"Image not found for description: {image_path}")
            return ""

        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            response = self.client.generate(
                model=self.description_model,
                prompt="Provide a detailed natural language description of this image. "
                       "Output ONLY the description. Do not include any preamble, "
                       "introductory text, conversational filler, or Markdown headings.",
                images=[image_bytes]
            )
            return response.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Failed to generate description for {image_path}: {e}")
            return ""

    def embed_image(self, image_path: Path) -> Dict[str, List[float]]:
        """
        Generates DINOv2 and CLIP embeddings for an image using Hugging Face Transformers.
        """
        image_path = Path(image_path)
        embeddings = {}
        
        if not image_path.exists():
            logger.warning(f"Image not found for embedding: {image_path}")
            return embeddings

        try:
            image = Image.open(image_path).convert("RGB")
            
            # DINOv2
            processor, model = self._get_dino()
            if processor and model:
                try:
                    inputs = processor(images=image, return_tensors="pt")
                    with torch.no_grad():
                        outputs = model(**inputs)
                    # DINOv2: use last_hidden_state mean or pooler_output if available.
                    # Dinov2Model usually outputs last_hidden_state.
                    # Common strategy: CLS token (index 0) or mean pooling.
                    # DINOv2 usually has a CLS token.
                    last_hidden_state = outputs.last_hidden_state
                    embedding = last_hidden_state.mean(dim=1) # Average pooling
                    embeddings["dino"] = embedding[0].tolist()
                except Exception as e:
                    logger.warning(f"Failed DINOv2 embedding execution: {e}")

            # CLIP
            processor, model = self._get_clip()
            if processor and model:
                try:
                    inputs = processor(images=image, return_tensors="pt")
                    with torch.no_grad():
                        outputs = model.get_image_features(**inputs)
                    embeddings["clip"] = outputs[0].tolist()
                except Exception as e:
                    logger.warning(f"Failed CLIP embedding execution: {e}")
                
        except Exception as e:
            logger.warning(f"Unexpected error during embedding for {image_path}: {e}")
            
        return embeddings