import pytest
import hashlib
from pathlib import Path
from extractor.utils import get_file_metadata

def test_get_file_metadata(tmp_path):
    # Create a test file with known content
    content = b"Hello, Conductor!"
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    expected_size = len(content)
    
    metadata = get_file_metadata(test_file)
    
    assert metadata["file_size"] == expected_size
    assert metadata["hash"] == expected_hash
    assert "creation_date" in metadata
    assert metadata["source_path"] == str(test_file.absolute())

def test_get_file_metadata_nonexistent(tmp_path):
    non_existent = tmp_path / "nope.txt"
    with pytest.raises(FileNotFoundError):
        get_file_metadata(non_existent)
