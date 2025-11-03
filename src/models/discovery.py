"""Pydantic models for Discovery phase (Phase 1)"""

from datetime import datetime

from pydantic import BaseModel


class TestFile(BaseModel):
    """Represents a discovered test file"""

    path: str
    last_modified: datetime


class DiscoverySummary(BaseModel):
    """Summary statistics for discovery phase"""

    total_files: int


class DiscoveryResult(BaseModel):
    """Output from Phase 1: Discovery"""

    timestamp: datetime
    repository: str
    summary: DiscoverySummary
    test_files: list[TestFile]

    def get_file(self, file_path: str) -> TestFile | None:
        """Get a test file by path"""
        return next((f for f in self.test_files if f.path == file_path), None)

    def get_changed_files(self) -> list[str]:
        """Get list of all file paths"""
        return [f.path for f in self.test_files]
