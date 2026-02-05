import pytest
from extractor.docling_engine import DoclingEngine

def test_docling_engine_initialization():
    engine = DoclingEngine()
    assert engine is not None
