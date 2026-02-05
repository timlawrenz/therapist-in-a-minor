from pathlib import Path
from typing import Generator, Set

class Scanner:
    SUPPORTED_EXTENSIONS: Set[str] = {
        # PDF
        '.pdf',
        # Image
        '.jpg', '.jpeg', '.png', '.tiff', '.bmp',
        # Video
        '.mp4', '.avi', '.mov', '.mkv'
    }

    def __init__(self, source_path: Path):
        self.source_path = Path(source_path)

    def scan(self) -> Generator[Path, None, None]:
        """
        Recursively yields paths to supported files in the source directory.
        Ignores hidden files (starting with .).
        If source_path is a file, yields it if supported.
        """
        if not self.source_path.exists():
            return

        if self.source_path.is_file():
            if self.source_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                yield self.source_path
            return

        for path in self.source_path.rglob('*'):
            # simple check to skip hidden files/dirs effectively? 
            # rglob('*') iterates everything. 
            # To strictly ignore hidden dirs during traversal, os.walk is better. 
            # But let's stick to a simple implementation first that passes tests.
            # Checking parts for hidden components ensures we don't process files in hidden dirs.
            
            if any(part.startswith('.') for part in path.relative_to(self.source_path).parts):
                continue
                
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                yield path
