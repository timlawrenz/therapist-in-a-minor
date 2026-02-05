from pathlib import Path

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
        
        # Folder is named after the document ID (filename without extension)
        # and placed in the same relative subdirectory structure.
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
