import pytest
from pathlib import Path
from extractor.scaffolding import Scaffolder

def test_is_processed_returns_false_if_no_manifest(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    
    scaffolder = Scaffolder(source_root, target_root)
    target_folder = target_root / "doc1"
    
    assert scaffolder.is_processed(target_folder) is False

def test_is_processed_returns_true_if_manifest_exists(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    
    scaffolder = Scaffolder(source_root, target_root)
    target_folder = target_root / "doc1"
    target_folder.mkdir()
    (target_folder / "manifest.json").touch()
    
    assert scaffolder.is_processed(target_folder) is True
