"""Minimal tests for Pydantic models"""

from datetime import datetime

from src.models import (
    DiscoveryResult,
    DiscoverySummary,
    ExtractionResult,
    ExtractionSummary,
    TestBlock,
    TestFile,
    TestFileAnalysis,
)


def test_test_file_model():
    """Test TestFile model creation"""
    test_file = TestFile(path="test.py", last_modified=datetime.now())
    assert test_file.path == "test.py"


def test_discovery_result_model():
    """Test DiscoveryResult model and methods"""
    test_file = TestFile(path="test.py", last_modified=datetime.now())

    summary = DiscoverySummary(total_files=1)

    result = DiscoveryResult(
        timestamp=datetime.now(), repository="test-repo", summary=summary, test_files=[test_file]
    )

    assert result.summary.total_files == 1
    assert result.get_file("test.py") == test_file


def test_test_block_model():
    """Test TestBlock model creation"""
    block = TestBlock(
        test_name="test_example",
        line_range="1-5",
        features_tested=["feature1"],
        feature_classification="user-facing",
        use_case_category="Testing",
        specific_use_case="When user wants to test",
        target_users=["developers"],
        complexity="simple",
        key_concepts=["testing"],
        user_value="Shows how to test",
    )

    assert block.test_name == "test_example"
    assert block.complexity == "simple"


def test_extraction_result_model():
    """Test ExtractionResult model"""
    block = TestBlock(
        test_name="test_example",
        line_range="1-5",
        features_tested=["feature1"],
        feature_classification="user-facing",
        complexity="simple",
        key_concepts=["testing"],
    )

    analysis = TestFileAnalysis(source_file="test.py", test_blocks=[block])

    summary = ExtractionSummary(total_test_blocks=1)

    result = ExtractionResult(
        timestamp=datetime.now(), repository="test-repo", summary=summary, test_analysis=[analysis]
    )

    assert result.summary.total_test_blocks == 1
    assert len(result.test_analysis) == 1
    assert result.test_analysis[0].source_file == "test.py"
    assert len(result.test_analysis[0].test_blocks) == 1
