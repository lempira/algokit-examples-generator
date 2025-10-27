"""Utility to read test files"""

from pathlib import Path


class CodeFileReader:
    """Reads code files from the repository"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    async def read(self, file_path: str) -> str:
        """Read a file's contents
        
        Args:
            file_path: Relative path from repo root or absolute path
            
        Returns:
            File contents as string
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.repo_path / path

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return path.read_text(encoding="utf-8")

    def read_sync(self, file_path: str) -> str:
        """Synchronous version of read"""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.repo_path / path

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return path.read_text(encoding="utf-8")

    def exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.repo_path / path
        return path.exists()

