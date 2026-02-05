from docling.document_converter import DocumentConverter

class DoclingEngine:
    """
    Wrapper for Docling's DocumentConverter to handle extraction.
    """
    def __init__(self):
        self.converter = DocumentConverter()
