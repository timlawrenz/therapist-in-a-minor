import os
from pathlib import Path
from typing import Dict, Any, Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_HERON_101, LayoutModelConfig
from docling.document_converter import DocumentConverter, PdfFormatOption
from extractor.utils import load_config

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
        if ocr_model_id:
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

    def save_images(self, result, output_dir: Path):
        """
        Saves extracted images to the specified directory and returns metadata.
        """
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
                    
                        image_metadata.append({
                            "filename": filename,
                            "page_no": page_no,
                            "bbox": bbox,
                            "path": str(output_dir / filename)
                        })
        
        return image_metadata

    def generate_manifest(self, result, output_path: Path, image_metadata: list):
        """
        Generates a manifest file with extraction metadata.
        """
        import json
        from datetime import datetime
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "page_count": len(result.pages) if hasattr(result, "pages") else 0,
            "models": {
                "ocr_model": self.config.get("docling", {}).get("ocr_model"),
                "layout_model": self.config.get("docling", {}).get("layout_model"),
            },
            "images": image_metadata,
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
