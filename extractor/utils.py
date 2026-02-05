import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extracts basic metadata from a file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Calculate SHA-256 hash
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    file_hash = sha256_hash.hexdigest()
    
    # Get stats
    stats = file_path.stat()
    
    return {
        "source_path": str(file_path.absolute()),
        "file_size": stats.st_size,
        "hash": file_hash,
        "creation_date": datetime.fromtimestamp(stats.st_ctime).isoformat(),
    }
