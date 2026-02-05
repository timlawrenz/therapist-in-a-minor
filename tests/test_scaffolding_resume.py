import pytest
import json
from pathlib import Path
from extractor.scaffolding import Scaffolder

@pytest.fixture
def scaffolder(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    return Scaffolder(source, target)

def test_is_extraction_complete_all_files_exist(scaffolder, tmp_path):
    target_folder = tmp_path / "target" / "doc1"
    target_folder.mkdir(parents=True)
    
    # Create manifest
    manifest = {
        "images": [
            {"filename": "img1.png"}
        ]
    }
    (target_folder / "manifest.json").write_text(json.dumps(manifest))
    
    # Create mandatory files
    (target_folder / "doc1.md").touch()
    (target_folder / "doc1.json").touch()
    
    # Create images directory and files
    images_dir = target_folder / "images"
    images_dir.mkdir()
    (images_dir / "img1.png").touch()
    (images_dir / "image_metadata.json").touch()
    
    assert scaffolder.is_extraction_complete(target_folder, "doc1") is True

def test_is_extraction_complete_missing_manifest(scaffolder, tmp_path):
    target_folder = tmp_path / "target" / "doc1"
    target_folder.mkdir(parents=True)
    assert scaffolder.is_extraction_complete(target_folder, "doc1") is False

def test_is_extraction_complete_missing_md(scaffolder, tmp_path):
    target_folder = tmp_path / "target" / "doc1"
    target_folder.mkdir(parents=True)
    (target_folder / "manifest.json").write_text("{}")
    (target_folder / "doc1.json").touch()
    assert scaffolder.is_extraction_complete(target_folder, "doc1") is False

def test_is_extraction_complete_missing_json(scaffolder, tmp_path):
    target_folder = tmp_path / "target" / "doc1"
    target_folder.mkdir(parents=True)
    (target_folder / "manifest.json").write_text("{}")
    (target_folder / "doc1.md").touch()
    assert scaffolder.is_extraction_complete(target_folder, "doc1") is False

def test_is_extraction_complete_missing_image(scaffolder, tmp_path):
    target_folder = tmp_path / "target" / "doc1"
    target_folder.mkdir(parents=True)
    
    manifest = {
        "images": [
            {"filename": "img1.png"}
        ]
    }
    (target_folder / "manifest.json").write_text(json.dumps(manifest))
    (target_folder / "doc1.md").touch()
    (target_folder / "doc1.json").touch()
    
    # Missing images dir or file
    assert scaffolder.is_extraction_complete(target_folder, "doc1") is False

def test_is_extraction_complete_missing_image_metadata(scaffolder, tmp_path):
    target_folder = tmp_path / "target" / "doc1"
    target_folder.mkdir(parents=True)
    
    manifest = {
        "images": [
            {"filename": "img1.png"}
        ]
    }
    (target_folder / "manifest.json").write_text(json.dumps(manifest))
    (target_folder / "doc1.md").touch()
    (target_folder / "doc1.json").touch()
    
    images_dir = target_folder / "images"
    images_dir.mkdir()
    (images_dir / "img1.png").touch()
    
    # Missing image_metadata.json
    assert scaffolder.is_extraction_complete(target_folder, "doc1") is False

def test_is_extraction_complete_no_images_success(scaffolder, tmp_path):
    target_folder = tmp_path / "target" / "doc1"
    target_folder.mkdir(parents=True)
    
    manifest = {
        "images": []
    }
    (target_folder / "manifest.json").write_text(json.dumps(manifest))
    (target_folder / "doc1.md").touch()
    (target_folder / "doc1.json").touch()
    
    # No images required, so image_metadata.json is not required
    assert scaffolder.is_extraction_complete(target_folder, "doc1") is True
