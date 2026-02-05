# Tech Stack - DOJ Disclosures HR4405 Derivative Dataset

## Core Language & Runtime
- **Python 3.10+**: Chosen for its dominance in PDF processing, OCR, and Machine Learning workflows.

## PDF Processing & Extraction
- **Docling**: Primary engine for parsing PDFs, performing layout-aware text extraction, and converting document structures into machine-readable formats.

## AI Enrichment & Computer Vision
- **Hugging Face Transformers / Accelerate**: The framework for running Vision-Language Models (VLMs) for image description and generating DINO/CLIP embeddings.
- **Ollama**: Local inference engine for running Vision-Language Models (VLMs) like LLaVA or Gemma 3 to generate image descriptions.
- **OpenCV / Pillow**: For pre-processing extracted images (cropping, resizing, format conversion) prior to AI analysis.

## Data Storage & Lineage
- **File-Based JSON Sidecars**: The source of truth for all metadata and lineage. Each source document will have a corresponding JSON manifest linking extracted assets to their origin. No centralized database engine is required for the core dataset.

## Pipeline Orchestration
- **Python CLI (Click/Argparse)**: A streamlined command-line interface to execute the extraction pipeline on specific files or recursively on directories.
