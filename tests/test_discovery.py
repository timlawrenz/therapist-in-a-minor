import pytest
from pathlib import Path
from extractor.discovery import Scanner

def test_scanner_finds_supported_files(tmp_path):
    # Setup: Create a nested directory structure with mixed files
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    # Supported files
    (source_dir / "doc1.pdf").touch()
    (source_dir / "image1.jpg").touch()
    (source_dir / "video1.mp4").touch()
    
    # Nested directory
    nested_dir = source_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "doc2.PDF").touch() # Case insensitivity check
    (nested_dir / "image2.PNG").touch()
    
    # Unsupported files
    (source_dir / "ignore.txt").touch()
    (nested_dir / "script.py").touch()
    
    scanner = Scanner(source_dir)
    found_files = list(scanner.scan())
    
    # Verification
    expected_files = {
        source_dir / "doc1.pdf",
        source_dir / "image1.jpg",
        source_dir / "video1.mp4",
        nested_dir / "doc2.PDF",
        nested_dir / "image2.PNG"
    }
    
    assert len(found_files) == 5
    assert set(found_files) == expected_files

def test_scanner_empty_directory(tmp_path):
    scanner = Scanner(tmp_path)
    assert list(scanner.scan()) == []

def test_scanner_ignores_hidden_files(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / ".hidden.pdf").touch()
    
    scanner = Scanner(source_dir)
    assert list(scanner.scan()) == []
