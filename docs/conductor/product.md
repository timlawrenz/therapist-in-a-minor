# Initial Concept

The project aims to create a derivative dataset from the DOJ Disclosures of HR4405 (The Epstein files). The goal is to convert the existing dataset (PDFs) into a machine-readable format (Markdown, images) while preserving the lineage and connections to the source files.

Key requirements:
- Extract text and images from PDFs (e.g., `DOJ Disclosures/HR4405/DataSet 2/VOL00002/IMAGES/0001/EFTA0000123456.pdf`).
- Maintain the original PDF.
- Create a new Markdown file containing the text.
- Save extracted images as separate files.
- Establish a manifest, folder structure, or database to link extracted text and images back to the original PDF.
- Support recursive processing (e.g., OCR on images, VLM descriptions, DINO/CLIP embeddings).

# Product Guide - DOJ Disclosures HR4405 Derivative Dataset

## Vision
Create a high-fidelity, machine-readable derivative of the DOJ Disclosures of HR4405 (The Epstein Files) that preserves absolute lineage to the original source documents while enabling modern data analysis and machine learning workflows.

## Target Audience
- **Researchers and Data Journalists:** Investigating the files with advanced search and cross-referencing tools.
- **Legal Analysts and Historians:** Requiring verifiable source attribution for every piece of extracted information.
- **Machine Learning Engineers:** Utilizing the dataset for training LLMs, VLMs, and entity extraction models.

## Core Goals
1. **Source Lineage Preservation:** Maintain a strict 1-to-1 mapping between extracted assets (text, images) and their origin (PDF file, page number, coordinates).
2. **Structural Integrity:** Mirror the original DOJ hierarchical folder structure to ensure familiarity and ease of navigation.
3. **ML Interoperability:** Provide data in formats ready for ingestion into modern training pipelines (Markdown, JSON, and future exports like Parquet).
4. **Enriched Searchability:** Enable future vector search and metadata filtering by preparing the foundation for AI-driven enrichment.
5. **Entity Foundation:** Structure data to facilitate a subsequent phase of entity extraction and relationship mapping in a graph database.

## Key Features
- **Hierarchical Extraction:** A processing pipeline that mirrors the source directory structure, creating sidecar Markdown files for text and sub-directories for images.
- **Resumable Processing:** Intelligent skipping of already-processed documents to facilitate efficient batch processing and recovery from interruptions.
- **Layout-Aware Text Extraction:** Capture text while attempting to preserve columns, tables, and headers to maintain context.
- **Asset Manifests:** JSON sidecars for every PDF that link every text block and image to its precise location in the original document.
- **Multimodal Enrichment:**
    - Integrated OCR for scanned documents.
    - Vision-Language Model (VLM) descriptions for extracted images.
    - Support for DINO/CLIP embeddings for visual search.

## Success Criteria
- All extracted text and images can be traced back to the exact page and coordinates of the source PDF.
- The output structure is navigable without specialized tools.
- The dataset passes initial validation for ingestion into a RAG (Retrieval-Augmented Generation) or ML training pipeline.

