import json
from pathlib import Path
from datetime import datetime
from .utils import get_file_metadata

class Scaffolder:
    def __init__(self, source_root: Path, target_root: Path):
        self.source_root = Path(source_root)
        self.target_root = Path(target_root)

    def get_target_folder(self, source_file: Path) -> Path:
        """
        Calculates the target folder path for a given source file.
        """
        source_file = Path(source_file)
        relative_path = source_file.relative_to(self.source_root)
        
        doc_id = source_file.stem
        target_folder = self.target_root / relative_path.parent / doc_id
        return target_folder

    def create_scaffold(self, source_file: Path) -> Path:
        """
        Creates the target directory structure for a given source file.
        """
        target_folder = self.get_target_folder(source_file)
        target_folder.mkdir(parents=True, exist_ok=True)
        return target_folder

    def write_manifest(self, source_file: Path, target_folder: Path) -> Path:
        """
        Generates and writes the manifest.json file.
        """
        source_file = Path(source_file)
        target_folder = Path(target_folder)
        
        metadata = get_file_metadata(source_file)
        
        # Determine file type
        ext = source_file.suffix.lower()
        file_type = "UNKNOWN"
        if ext == '.pdf':
            file_type = "PDF"
        elif ext in {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}:
            file_type = "IMAGE"
        elif ext in {'.mp4', '.avi', '.mov', '.mkv'}:
            file_type = "VIDEO"

        manifest_data = {
            "document_id": source_file.stem,
            "source_path": metadata["source_path"],
            "file_type": file_type,
            "file_size": metadata["file_size"],
            "hash": metadata["hash"],
            "creation_date": metadata["creation_date"],
            "processing_history": [
                {
                    "step": "discovery",
                    "timestamp": datetime.now().isoformat(),
                    "status": "success"
                }
            ]
        }
        
        manifest_path = target_folder / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)
            
        return manifest_path

    def link_source(self, source_file: Path, target_folder: Path):
        """
        Creates a symlink to the source file in the target folder.
        """
        source_file = Path(source_file).absolute()
        target_folder = Path(target_folder)
        
        link_path = target_folder / source_file.name
        if link_path.exists():
            link_path.unlink()
            
        link_path.symlink_to(source_file)