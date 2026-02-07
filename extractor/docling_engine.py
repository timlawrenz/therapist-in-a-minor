import os
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_HERON_101, LayoutModelConfig
from docling.document_converter import DocumentConverter, PdfFormatOption
from extractor.utils import load_config, get_file_metadata

logger = logging.getLogger(__name__)

class DoclingEngine:
    """
    Wrapper for Docling's DocumentConverter to handle extraction.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the DoclingEngine with configuration.
        """
        self.config = config or load_config()
        
        # Initialize pipeline options
        pipeline_options = PdfPipelineOptions()
        
        # Configure models from config
        docling_config = self.config.get("docling", {})
        
        # Layout model configuration
        layout_model_id = docling_config.get("layout_model")
        if layout_model_id:
            if "docling-layout-heron-101" in layout_model_id:
                pipeline_options.layout_options.model_spec = DOCLING_LAYOUT_HERON_101
            else:
                repo_id = layout_model_id.split("huggingface.co/")[-1]
                pipeline_options.layout_options.model_spec = LayoutModelConfig(
                    name="custom_layout",
                    repo_id=repo_id,
                    revision="main",
                    model_path=""
                )
            
        # OCR configuration
        ocr_model_id = docling_config.get("ocr_model")
        if "do_ocr" in docling_config:
            pipeline_options.do_ocr = bool(docling_config.get("do_ocr"))
        elif ocr_model_id:
            pipeline_options.do_ocr = True
    
        # Enable image extraction as per vision
        pipeline_options.generate_picture_images = True
            
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def convert(self, pdf_path: Path):
        """
        Converts a PDF document.
        """
        return self.converter.convert(pdf_path)

    def save_markdown(self, result, output_path: Path):
        """
        Saves the conversion result as Markdown.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # docling result.document is a DoclingDocument which supports export_to_markdown
        md_content = result.document.export_to_markdown()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

    def save_json(self, result, output_path: Path):
        """
        Saves the conversion result as JSON.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # docling result.document supports export_to_dict or model_dump (pydantic)
        # docling documents are pydantic models usually
        import json
        
        # Check if it has export_to_dict or model_dump
        if hasattr(result.document, "export_to_dict"):
            data = result.document.export_to_dict()
        elif hasattr(result.document, "model_dump"):
            data = result.document.model_dump()
        else:
            # Fallback or error
            raise ValueError("Document object does not support dictionary export")
            
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _extract_images_with_pdfimages(self, pdf_path: Path, output_dir: Path):
        """Best-effort fallback extraction for PDFs that contain only embedded XObject images.

        This is used only when Docling emits zero pictures.
        """
        if not pdf_path or not pdf_path.exists():
            return []
        if shutil.which("pdfimages") is None:
            return []

        prefix = output_dir / "pdfimage"
        try:
            subprocess.run(
                ["pdfimages", "-png", "-p", str(pdf_path), str(prefix)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.debug(f"pdfimages extraction failed for {pdf_path}: {e}")
            return []

        out = []
        pattern = re.compile(r"-(\d+)-(\d+)\.png$")
        for img_file in sorted(output_dir.glob(f"{prefix.name}-*.png")):
            m = pattern.search(img_file.name)
            if not m:
                continue

            page_no = int(m.group(1))
            img_idx = int(m.group(2)) + 1
            target_name = f"page_{page_no}_img_{img_idx}.png"
            target_path = output_dir / target_name

            if not target_path.exists():
                img_file.rename(target_path)
            else:
                target_path = img_file

            out.append(
                {
                    "filename": target_path.name,
                    "page_no": page_no,
                    "bbox": None,
                    "path": str(target_path),
                }
            )

        return out

    def save_images(self, result, output_dir: Path):
        """Saves extracted images to the specified directory and returns metadata."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_metadata = []

        # Check if document has pictures
        if hasattr(result.document, "pictures"):
            for i, picture in enumerate(result.document.pictures):
                # Check if picture has image data (PIL Image)
                if hasattr(picture, "image") and picture.image is not None:
                    # Try to get page number from provenance
                    page_no = 0
                    bbox = None
                    if hasattr(picture, "prov") and picture.prov:
                        # prov is a list of Prov items, usually one for the picture location
                        # Assuming Prov has page_no
                        page_no = picture.prov[0].page_no
                        if hasattr(picture.prov[0], "bbox") and picture.prov[0].bbox:
                            bbox = picture.prov[0].bbox.as_tuple()

                    filename = f"page_{page_no}_img_{i+1}.png"

                    # Handle Docling ImageRef
                    img = picture.image
                    if hasattr(img, "pil_image"):
                        img = img.pil_image

                    if img is not None:
                        img.save(output_dir / filename)
                        logger.debug(f"Extracted image: {filename} to {output_dir}")

                        image_metadata.append(
                            {
                                "filename": filename,
                                "page_no": page_no,
                                "bbox": bbox,
                                "path": str(output_dir / filename),
                            }
                        )

        if not image_metadata:
            pdf_path = None
            if hasattr(result, "input") and hasattr(result.input, "file"):
                pdf_path = Path(result.input.file)
            image_metadata = self._extract_images_with_pdfimages(pdf_path, output_dir)

        return image_metadata

    def generate_manifest(self, result, output_path: Path, image_metadata: list):
        """
        Generates a manifest file with extraction metadata.
        """
        import json
        from datetime import datetime

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        existing = {}
        if output_path.exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}

        manifest = dict(existing) if isinstance(existing, dict) else {}

        src_path = manifest.get("source_path")
        if not src_path:
            try:
                if hasattr(result, "input") and hasattr(result.input, "file") and result.input.file:
                    src_path = str(Path(result.input.file).absolute())
            except Exception:
                src_path = None

        if src_path:
            manifest.setdefault("source_path", src_path)
            src_file = Path(src_path)
            if src_file.exists():
                try:
                    meta = get_file_metadata(src_file)
                    for key in ("file_size", "hash", "creation_date"):
                        if key in meta:
                            manifest.setdefault(key, meta[key])
                    manifest.setdefault("document_id", src_file.stem)
                    manifest.setdefault("file_type", "PDF" if src_file.suffix.lower() == ".pdf" else "UNKNOWN")
                except Exception:
                    pass

        history = manifest.get("processing_history")
        if not isinstance(history, list):
            history = []

        now = datetime.now().isoformat()
        extraction_entry = {"step": "extraction", "timestamp": now, "status": "success"}
        for i in range(len(history) - 1, -1, -1):
            if isinstance(history[i], dict) and history[i].get("step") == "extraction":
                history[i] = extraction_entry
                break
        else:
            history.append(extraction_entry)

        manifest["processing_history"] = history

        manifest.update(
            {
                "timestamp": now,
                "page_count": len(result.pages) if hasattr(result, "pages") else 0,
                "models": {
                    "ocr_model": self.config.get("docling", {}).get("ocr_model"),
                    "layout_model": self.config.get("docling", {}).get("layout_model"),
                },
                "images": image_metadata,
            }
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
