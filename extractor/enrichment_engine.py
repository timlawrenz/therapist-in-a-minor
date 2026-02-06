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

        # Back-compat / convenience aliases
        if self.embedding_model_dino_id in {"dinov2", "dino"}:
            self.embedding_model_dino_id = "facebook/dinov2-base"
        if self.embedding_model_clip_id == "clip":
            self.embedding_model_clip_id = "openai/clip-vit-base-patch32"
        
        # Initialize Ollama client
        self.client = ollama.Client(host=self.ollama_host)
        
        # Lazy loading for HF models
        self._dino_processor = None
        self._dino_model = None
        self._clip_processor = None
        self._clip_model = None

        # Facial enrichment config (optional)
        facial_config = (enrichment_config.get("facial") or {})
        self.facial_enabled = bool(facial_config.get("enabled", False))
        self.facial_device = facial_config.get("device", "auto")

        retinaface_config = (facial_config.get("retinaface") or {})
        self.retinaface_model_id = retinaface_config.get("model")
        self.retinaface_min_confidence = float(retinaface_config.get("min_confidence", 0.8))

        facenet_config = (facial_config.get("facenet") or {})
        self.facenet_pretrained = facenet_config.get("pretrained", "vggface2")

        self._retinaface = None
        self._facenet = None

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
                prompt=(
                    "Provide a detailed natural language description of this image. "
                    "Output ONLY the description. Do not include any preamble, introductory text, "
                    "conversational filler, or Markdown headings. "
                    "If the image appears to be primarily a document (scanned page, form, letter, "
                    "screenshot of text, table), then after the description also include three plain-text "
                    "lines exactly in this format: 'Persons: ...', 'Locations: ...', 'Dates: ...'. "
                    "For each line, list every person name, location, and date you can read from the document; "
                    "if none are found, write 'Persons: (none)', etc."
                ),
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

    def _get_facial_device(self) -> torch.device:
        pref = str(self.facial_device or "auto").lower()
        if pref == "cpu":
            return torch.device("cpu")
        if pref in {"cuda", "gpu"}:
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _get_retinaface(self):
        if self._retinaface is False:
            return None
        if self._retinaface is not None:
            return self._retinaface

        try:
            from retinaface_pytorch import RetinaFace  # type: ignore

            self._retinaface = RetinaFace(device=str(self._get_facial_device()))
            return self._retinaface
        except Exception:
            try:
                from retinaface import RetinaFace  # type: ignore

                self._retinaface = RetinaFace
                return self._retinaface
            except Exception as e:
                logger.warning(f"RetinaFace dependency not available: {e}")
                self._retinaface = False
                return None

    def _detect_faces_retinaface(self, image: Image.Image) -> List[List[int]]:
        detector = self._get_retinaface()
        if not detector:
            return []

        try:
            import numpy as np

            np_img = np.asarray(image)
            if hasattr(detector, "detect_faces"):
                result = detector.detect_faces(np_img)
            elif callable(detector):
                result = detector(np_img)
            else:
                return []

            boxes: List[List[int]] = []

            if isinstance(result, dict):
                for face in result.values():
                    if not isinstance(face, dict):
                        continue
                    score = face.get("score", face.get("confidence", 1.0))
                    area = face.get("facial_area") or face.get("bbox") or face.get("box")
                    if area is None:
                        continue
                    if score is not None and float(score) < self.retinaface_min_confidence:
                        continue
                    x1, y1, x2, y2 = area
                    boxes.append([int(x1), int(y1), int(x2), int(y2)])

            elif isinstance(result, (list, tuple)) and result:
                if isinstance(result[0], dict):
                    for face in result:  # type: ignore[assignment]
                        score = face.get("score", face.get("confidence", 1.0))
                        area = face.get("facial_area") or face.get("bbox") or face.get("box")
                        if area is None:
                            continue
                        if score is not None and float(score) < self.retinaface_min_confidence:
                            continue
                        x1, y1, x2, y2 = area
                        boxes.append([int(x1), int(y1), int(x2), int(y2)])
                elif len(result[0]) == 4:
                    boxes = [[int(v) for v in box] for box in result]  # type: ignore[arg-type]

            return boxes
        except Exception as e:
            logger.warning(f"Failed to detect faces: {e}")
            return []

    def _get_facenet(self):
        if self._facenet is False:
            return None
        if self._facenet is not None:
            return self._facenet

        try:
            from facenet_pytorch import InceptionResnetV1  # type: ignore

            device = self._get_facial_device()
            self._facenet = InceptionResnetV1(pretrained=self.facenet_pretrained).eval().to(device)
            return self._facenet
        except Exception as e:
            logger.warning(f"FaceNet dependency not available: {e}")
            self._facenet = False
            return None

    def _embed_faces_facenet(self, face_images: List[Image.Image]) -> List[List[float]]:
        model = self._get_facenet()
        if not model or not face_images:
            return []

        try:
            import numpy as np

            device = self._get_facial_device()
            tensors = []
            for face in face_images:
                img = face.convert("RGB").resize((160, 160))
                arr = np.asarray(img).astype("float32") / 255.0
                t = torch.from_numpy(arr).permute(2, 0, 1)
                t = (t - 0.5) / 0.5
                tensors.append(t)

            batch = torch.stack(tensors, dim=0).to(device)
            with torch.no_grad():
                emb = model(batch)
            return emb.cpu().tolist()
        except Exception as e:
            logger.warning(f"Failed to embed faces: {e}")
            return []

    def extract_faces(self, image_path: Path) -> List[Dict[str, Any]]:
        if not self.facial_enabled:
            return []

        image_path = Path(image_path)
        if not image_path.exists():
            logger.warning(f"Image not found for face extraction: {image_path}")
            return []

        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to open image for face extraction {image_path}: {e}")
            return []

        bboxes_xyxy = self._detect_faces_retinaface(image)
        if not bboxes_xyxy:
            return []

        img_w, img_h = image.size
        face_crops: List[Image.Image] = []
        clipped_boxes: List[List[int]] = []
        for x1, y1, x2, y2 in bboxes_xyxy:
            x1 = max(0, min(int(x1), img_w - 1))
            y1 = max(0, min(int(y1), img_h - 1))
            x2 = max(0, min(int(x2), img_w))
            y2 = max(0, min(int(y2), img_h))
            if x2 <= x1 or y2 <= y1:
                continue
            clipped_boxes.append([x1, y1, x2, y2])
            face_crops.append(image.crop((x1, y1, x2, y2)))

        if not face_crops:
            return []

        embeddings = self._embed_faces_facenet(face_crops)
        if not embeddings:
            return []

        faces: List[Dict[str, Any]] = []
        for box, embedding in zip(clipped_boxes, embeddings):
            x1, y1, x2, y2 = box
            faces.append({
                "bbox": [x1, y1, x2 - x1, y2 - y1],
                "embedding": embedding,
            })

        return faces
