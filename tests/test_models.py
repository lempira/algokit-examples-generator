"""Minimal tests for Pydantic models"""

from datetime import datetime

import pytest

from src.models.phase_outputs import (
    DiscoveryResult,
    DiscoverySummary,
    ExtractionResult,
    ExtractionSummary,
    FileStatus,
    Prerequisites,
    TestBlock,
    TestFile,
    TestFileAnalysis,
)


def test_test_file_model():
    """Test TestFile model creation"""
    test_file = TestFile(
        path="test.py",
        sha256="abc123",
        status=FileStatus.CREATED,
        last_modified=datetime.now()
    )
    assert test_file.path == "test.py"
    assert test_file.status == FileStatus.CREATED


def test_discovery_result_model():
    """Test DiscoveryResult model and methods"""
    test_file = TestFile(
        path="test.py",
        sha256="abc123",
        status=FileStatus.UPDATED,
        last_modified=datetime.now()
    )
    
    summary = DiscoverySummary(
        total_files_discovered=1,
        total_files_tracked=1,
        created=0,
        updated=1,
        unchanged=0,
        deleted=0
    )
    
    result = DiscoveryResult(
        timestamp=datetime.now(),
        repository="test-repo",
        summary=summary,
        test_files=[test_file]
    )
    
    assert result.summary.total_files_discovered == 1
    assert result.get_file("test.py") == test_file
    assert result.get_changed_files() == ["test.py"]


def test_test_block_model():
    """Test TestBlock model creation"""
    prereqs = Prerequisites(
        imports=["test_lib"],
        setup_requirements=[],
        configuration=[]
    )
    
    block = TestBlock(
        test_name="test_example",
        line_range="1-5",
        features_tested=["feature1"],
        feature_classification="user-facing",
        use_case_category="Testing",
        specific_use_case="When user wants to test",
        target_users=["developers"],
        example_potential="high",
        complexity="simple",
        prerequisites=prereqs,
        key_concepts=["testing"],
        user_value="Shows how to test"
    )
    
    assert block.test_name == "test_example"
    assert block.example_potential == "high"


def test_extraction_result_model():
    """Test ExtractionResult model and methods"""
    prereqs = Prerequisites(
        imports=["test_lib"],
        setup_requirements=[],
        configuration=[]
    )
    
    block = TestBlock(
        test_name="test_example",
        line_range="1-5",
        features_tested=["feature1"],
        feature_classification="user-facing",
        example_potential="high",
        complexity="simple",
        prerequisites=prereqs,
        key_concepts=["testing"]
    )
    
    analysis = TestFileAnalysis(
        source_file="test.py",
        file_status=FileStatus.CREATED,
        test_blocks=[block]
    )
    
    summary = ExtractionSummary(
        total_test_blocks=1,
        from_created_files=1,
        from_updated_files=0,
        from_unchanged_files=0,
        from_deleted_files=0,
        potential_breakdown={"high": 1},
        complexity_breakdown={"simple": 1}
    )
    
    result = ExtractionResult(
        timestamp=datetime.now(),
        repository="test-repo",
        summary=summary,
        test_analysis=[analysis]
    )
    
    assert result.summary.total_test_blocks == 1
    assert len(result.get_high_potential_blocks()) == 1
    assert len(result.get_blocks_for_file("test.py")) == 1

