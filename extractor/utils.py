import hashlib
import os
import yaml
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

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Loads configuration from a YAML file.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    
    return config
