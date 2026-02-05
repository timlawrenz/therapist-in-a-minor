import pytest
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
