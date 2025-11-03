"""Tests for Discovery node"""

from src.nodes.discovery import DiscoveryNode
from src.utils.json_store import JSONStore


def test_discovery_first_run(tmp_path):
    """Test discovery finds test files"""
    # Create test files
    test_dir = tmp_path / "src" / "tests"
    test_dir.mkdir(parents=True)

    test_file1 = test_dir / "example.test.ts"
    test_file1.write_text("test content 1")

    test_file2 = test_dir / "test_feature.py"
    test_file2.write_text("test content 2")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery
    node = DiscoveryNode(tmp_path, json_store)
    result = node.run("test-repo")

    # Verify results
    assert result.repository == "test-repo"
    assert result.summary.total_files == 2
    assert len(result.test_files) == 2


def test_discovery_multiple_patterns(tmp_path):
    """Test discovery finds files matching different patterns"""
    # Create test files with different patterns
    test_dir = tmp_path / "src" / "tests"
    test_dir.mkdir(parents=True)

    (test_dir / "example.test.ts").write_text("ts test")
    (test_dir / "feature.spec.js").write_text("js spec")
    (test_dir / "test_python.py").write_text("python test")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery
    node = DiscoveryNode(tmp_path, json_store)
    result = node.run("test-repo")

    # Verify all patterns were found
    assert result.summary.total_files == 3
    paths = {f.path for f in result.test_files}
    assert "src/tests/example.test.ts" in paths
    assert "src/tests/feature.spec.js" in paths
    assert "src/tests/test_python.py" in paths


def test_discovery_saves_json(tmp_path):
    """Test that discovery saves results to JSON file"""
    # Create test file
    test_dir = tmp_path / "src" / "tests"
    test_dir.mkdir(parents=True)

    test_file = test_dir / "example.test.ts"
    test_file.write_text("test content")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery
    node = DiscoveryNode(tmp_path, json_store)
    node.run("test-repo")

    # Verify JSON file exists
    json_file = examples_dir / "01-discovery.json"
    assert json_file.exists()

    # Verify JSON content
    saved_data = json_store.read_sync("01-discovery.json")
    assert saved_data["repository"] == "test-repo"
    assert saved_data["summary"]["total_files"] == 1
    assert len(saved_data["test_files"]) == 1
