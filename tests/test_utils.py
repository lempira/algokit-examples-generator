"""Minimal tests for utility classes"""


from datetime import datetime

import pytest

from src.models.phase_outputs import (
    DiscoveryResult,
    DiscoverySummary,
    FileStatus,
    TestFile,
)
from src.utils.code_executor import CodeExecutor
from src.utils.file_reader import CodeFileReader
from src.utils.json_store import JSONStore


def test_file_reader(tmp_path):
    """Test CodeFileReader can read files"""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    reader = CodeFileReader(tmp_path)
    content = reader.read_sync("test.txt")

    assert content == "Hello, World!"
    assert reader.exists("test.txt")
    assert not reader.exists("nonexistent.txt")


def test_file_reader_file_not_found(tmp_path):
    """Test CodeFileReader raises error for missing files"""
    reader = CodeFileReader(tmp_path)

    with pytest.raises(FileNotFoundError):
        reader.read_sync("nonexistent.txt")


def test_json_store_write_and_read(tmp_path):
    """Test JSONStore can write and read JSON files"""
    store = JSONStore(tmp_path)

    # Test with dict
    data = {"key": "value", "number": 42}
    store.write_sync("test.json", data)

    read_data = store.read_sync("test.json")
    assert read_data == data
    assert store.exists("test.json")


def test_json_store_with_pydantic_model(tmp_path):
    """Test JSONStore can write Pydantic models"""
    store = JSONStore(tmp_path)

    test_file = TestFile(
        path="test.py",
        sha256="abc123",
        status=FileStatus.CREATED,
        last_modified=datetime.now()
    )

    summary = DiscoverySummary(
        total_files_discovered=1,
        total_files_tracked=1,
        created=1,
        updated=0,
        unchanged=0,
        deleted=0
    )

    result = DiscoveryResult(
        timestamp=datetime.now(),
        repository="test-repo",
        summary=summary,
        test_files=[test_file]
    )

    store.write_sync("discovery.json", result)

    read_data = store.read_sync("discovery.json")
    assert read_data["summary"]["total_files_discovered"] == 1
    assert len(read_data["test_files"]) == 1


def test_json_store_read_optional(tmp_path):
    """Test JSONStore read_optional returns None for missing files"""
    store = JSONStore(tmp_path)

    result = store.read_optional_sync("nonexistent.json")
    assert result is None

    # Write a file and verify it returns data
    store.write_sync("exists.json", {"test": True})
    result = store.read_optional_sync("exists.json")
    assert result == {"test": True}


def test_code_executor_nonexistent_path(tmp_path):
    """Test CodeExecutor handles nonexistent paths"""
    executor = CodeExecutor()
    result = executor.run_sync(tmp_path / "nonexistent")

    assert not result.success
    assert result.exit_code == -1
    assert "does not exist" in result.error_message


def test_code_executor_no_entry_point(tmp_path):
    """Test CodeExecutor handles examples with no entry point"""
    # Create empty example directory
    example_dir = tmp_path / "example"
    example_dir.mkdir()

    executor = CodeExecutor()
    result = executor.run_sync(example_dir)

    assert not result.success
    assert "No recognized entry point" in result.error_message

