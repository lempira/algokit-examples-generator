"""Tests for Discovery node"""



from src.models.phase_outputs import FileStatus
from src.nodes.discovery import DiscoveryNode
from src.utils.json_store import JSONStore


def test_discovery_first_run(tmp_path):
    """Test discovery on first run (no previous data)"""
    # Create test files
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

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
    assert result.summary.total_files_discovered == 2
    assert result.summary.created == 2
    assert result.summary.updated == 0
    assert result.summary.unchanged == 0
    assert result.summary.deleted == 0

    # Verify all files are marked as created
    assert len(result.test_files) == 2
    for test_file in result.test_files:
        assert test_file.status == FileStatus.CREATED
        assert len(test_file.sha256) == 64  # SHA-256 hex length


def test_discovery_incremental_unchanged(tmp_path):
    """Test discovery with unchanged files"""
    # Create test file
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    test_file = test_dir / "example.test.ts"
    test_file.write_text("test content")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery first time
    node = DiscoveryNode(tmp_path, json_store)
    node.run("test-repo")

    # Run discovery second time (no changes)
    second_result = node.run("test-repo")

    # Verify file is marked as unchanged
    assert second_result.summary.total_files_discovered == 1
    assert second_result.summary.created == 0
    assert second_result.summary.updated == 0
    assert second_result.summary.unchanged == 1
    assert second_result.summary.deleted == 0

    assert second_result.test_files[0].status == FileStatus.UNCHANGED


def test_discovery_incremental_updated(tmp_path):
    """Test discovery with updated file"""
    # Create test file
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    test_file = test_dir / "example.test.ts"
    test_file.write_text("test content v1")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery first time
    node = DiscoveryNode(tmp_path, json_store)
    first_result = node.run("test-repo")
    first_hash = first_result.test_files[0].sha256

    # Modify the file
    test_file.write_text("test content v2 - modified")

    # Run discovery second time
    second_result = node.run("test-repo")

    # Verify file is marked as updated
    assert second_result.summary.total_files_discovered == 1
    assert second_result.summary.created == 0
    assert second_result.summary.updated == 1
    assert second_result.summary.unchanged == 0
    assert second_result.summary.deleted == 0

    assert second_result.test_files[0].status == FileStatus.UPDATED
    assert second_result.test_files[0].sha256 != first_hash


def test_discovery_incremental_deleted(tmp_path):
    """Test discovery with deleted file"""
    # Create test file
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    test_file = test_dir / "example.test.ts"
    test_file.write_text("test content")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery first time
    node = DiscoveryNode(tmp_path, json_store)
    node.run("test-repo")

    # Delete the file
    test_file.unlink()

    # Run discovery second time
    second_result = node.run("test-repo")

    # Verify file is marked as deleted
    assert second_result.summary.total_files_discovered == 0
    assert second_result.summary.total_files_tracked == 1
    assert second_result.summary.created == 0
    assert second_result.summary.updated == 0
    assert second_result.summary.unchanged == 0
    assert second_result.summary.deleted == 1

    assert second_result.test_files[0].status == FileStatus.DELETED


def test_discovery_incremental_new_file(tmp_path):
    """Test discovery with new file added"""
    # Create initial test file
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    test_file1 = test_dir / "example.test.ts"
    test_file1.write_text("test content 1")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery first time
    node = DiscoveryNode(tmp_path, json_store)
    node.run("test-repo")

    # Add a new file
    test_file2 = test_dir / "new_feature.test.ts"
    test_file2.write_text("test content 2")

    # Run discovery second time
    second_result = node.run("test-repo")

    # Verify summary
    assert second_result.summary.total_files_discovered == 2
    assert second_result.summary.created == 1
    assert second_result.summary.updated == 0
    assert second_result.summary.unchanged == 1
    assert second_result.summary.deleted == 0

    # Verify file statuses
    statuses = {f.path: f.status for f in second_result.test_files}
    assert statuses["tests/example.test.ts"] == FileStatus.UNCHANGED
    assert statuses["tests/new_feature.test.ts"] == FileStatus.CREATED


def test_discovery_multiple_patterns(tmp_path):
    """Test discovery finds files matching different patterns"""
    # Create test files with different patterns
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

    (test_dir / "example.test.ts").write_text("ts test")
    (test_dir / "feature.spec.js").write_text("js spec")
    (test_dir / "test_python.py").write_text("python test")
    (test_dir / "utils_test.go").write_text("go test")
    (test_dir / "ruby_test.rb").write_text("ruby test")

    # Create JSON store
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    json_store = JSONStore(examples_dir)

    # Run discovery
    node = DiscoveryNode(tmp_path, json_store)
    result = node.run("test-repo")

    # Verify all patterns were found
    assert result.summary.total_files_discovered == 5
    paths = {f.path for f in result.test_files}
    assert "tests/example.test.ts" in paths
    assert "tests/feature.spec.js" in paths
    assert "tests/test_python.py" in paths
    assert "tests/utils_test.go" in paths
    assert "tests/ruby_test.rb" in paths


def test_discovery_saves_json(tmp_path):
    """Test that discovery saves results to JSON file"""
    # Create test file
    test_dir = tmp_path / "tests"
    test_dir.mkdir()

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
    assert saved_data["summary"]["total_files_discovered"] == 1
    assert len(saved_data["test_files"]) == 1

