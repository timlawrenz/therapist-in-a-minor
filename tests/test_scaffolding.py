import pytest
import json
from pathlib import Path
from extractor.scaffolding import Scaffolder

def test_scaffolder_calculates_correct_target_path(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    
    # Nested file
    source_file = source_root / "dataset1" / "vol1" / "doc1.pdf"
    source_file.parent.mkdir(parents=True)
    source_file.touch()
    
    scaffolder = Scaffolder(source_root, target_root)
    target_folder = scaffolder.get_target_folder(source_file)
    
    expected_folder = target_root / "dataset1" / "vol1" / "doc1"
    assert target_folder == expected_folder

def test_scaffolder_creates_directory(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    
    source_file = source_root / "doc1.pdf"
    source_file.touch()
    
    scaffolder = Scaffolder(source_root, target_root)
    target_folder = scaffolder.create_scaffold(source_file)
    
    assert target_folder.exists()
    assert target_folder.is_dir()
    assert target_folder.name == "doc1"

def test_scaffolder_writes_manifest(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    
    source_file = source_root / "doc1.pdf"
    source_file.write_text("dummy content")
    
    scaffolder = Scaffolder(source_root, target_root)
    target_folder = scaffolder.create_scaffold(source_file)
    manifest_path = scaffolder.write_manifest(source_file, target_folder)
    
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        data = json.load(f)
        
    assert data["document_id"] == "doc1"
    assert data["file_type"] == "PDF"
    assert "hash" in data
    assert "processing_history" in data
    assert data["processing_history"][0]["step"] == "discovery"

def test_scaffolder_links_source_file(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    
    source_file = source_root / "doc1.pdf"
    source_file.write_text("dummy content")
    
    scaffolder = Scaffolder(source_root, target_root)
    target_folder = scaffolder.create_scaffold(source_file)
    scaffolder.link_source(source_file, target_folder)
    
    linked_file = target_folder / "doc1.pdf"
    assert linked_file.exists()
    assert linked_file.is_symlink()