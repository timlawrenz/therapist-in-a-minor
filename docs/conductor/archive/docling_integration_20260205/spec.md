# Specification: Docling Integration for PDF Extraction

## Overview
This track involves integrating the `docling` library into the `extractor` tool to enhance PDF processing. `docling` will be used as the primary engine for layout-aware text extraction, image extraction, and document structure analysis, specifically utilizing advanced Hugging Face models for OCR and layout detection.

## Functional Requirements
- **Library Integration:** Add `docling` and its dependencies to `requirements.txt`.
- **Model Configuration:** Implement a configuration system (e.g., `config.yaml`) to specify the use of `https://huggingface.co/zai-org/GLM-OCR` for OCR and `https://huggingface.co/docling-project/docling-layout-heron-101` for layout analysis.
- **CLI Update:** Modify the existing `extract` command in `extractor/cli.py` to use `docling` by default for all PDF processing.
- **Enhanced Extraction:**
    - Extract document structure into a full JSON representation.
    - Generate high-fidelity Markdown files.
    - Extract and save images as individual files in a mirrored directory structure.
    - Generate a metadata summary (page count, models used, etc.) for each processed document.
- **Lineage Preservation:** Ensure every extracted text block and image includes coordinates and page references back to the source PDF.

## Non-Functional Requirements
- **Mirrored Structure:** The output must strictly mirror the original directory structure of the source PDFs.
- **Table Support:** Ensure accurate conversion of PDF tables into Markdown table format.

## Acceptance Criteria
- [ ] `docling` is successfully installed and integrated.
- [ ] Processing a PDF correctly loads and uses the GLM-OCR and Heron-101 models.
- [ ] Output includes: JSON structure, Markdown, extracted images, and a manifest/metadata file.
- [ ] Every extracted asset is traceable back to its source coordinates.
- [ ] The `extract` CLI command works as expected with the new engine.
- [ ] Automated tests verify extraction accuracy and lineage mapping.

## Out of Scope
- Training or fine-tuning the Hugging Face models.
- Support for non-PDF file formats in this track.
