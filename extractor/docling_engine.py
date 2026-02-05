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
