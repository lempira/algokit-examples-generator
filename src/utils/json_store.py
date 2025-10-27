"""Utility to read/write phase JSON files"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class JSONStore:
    """Manages reading and writing phase JSON files"""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.mkdir(parents=True, exist_ok=True)

    async def write(self, filename: str, data: BaseModel | dict) -> None:
        """Write data to a JSON file
        
        Args:
            filename: Name of the file (e.g., "01-discovery.json")
            data: Pydantic model or dict to write
        """
        file_path = self.output_path / filename

        # Convert Pydantic model to dict if needed
        if isinstance(data, BaseModel):
            json_data = data.model_dump(mode="json")
        else:
            json_data = data

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, default=str)

    def write_sync(self, filename: str, data: BaseModel | dict) -> None:
        """Synchronous version of write"""
        file_path = self.output_path / filename

        if isinstance(data, BaseModel):
            json_data = data.model_dump(mode="json")
        else:
            json_data = data

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, default=str)

    async def read(self, filename: str) -> dict[str, Any]:
        """Read data from a JSON file
        
        Args:
            filename: Name of the file (e.g., "01-discovery.json")
            
        Returns:
            Parsed JSON data as dict
        """
        file_path = self.output_path / filename

        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def read_sync(self, filename: str) -> dict[str, Any]:
        """Synchronous version of read"""
        file_path = self.output_path / filename

        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    async def read_optional(self, filename: str) -> dict[str, Any] | None:
        """Read a JSON file if it exists, otherwise return None
        
        Args:
            filename: Name of the file
            
        Returns:
            Parsed JSON data or None if file doesn't exist
        """
        file_path = self.output_path / filename

        if not file_path.exists():
            return None

        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def read_optional_sync(self, filename: str) -> dict[str, Any] | None:
        """Synchronous version of read_optional"""
        file_path = self.output_path / filename

        if not file_path.exists():
            return None

        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def exists(self, filename: str) -> bool:
        """Check if a JSON file exists"""
        return (self.output_path / filename).exists()

