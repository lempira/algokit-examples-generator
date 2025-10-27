"""Phase 1: Discovery Node - Find and track test files"""

import hashlib
from datetime import datetime
from pathlib import Path

from ..models.phase_outputs import (
    DiscoveryResult,
    DiscoverySummary,
    FileStatus,
    TestFile,
)
from ..utils.json_store import JSONStore


class DiscoveryNode:
    """Phase 1: Discover test files and track changes"""

    # Test file patterns by language
    TEST_PATTERNS = [
        # TypeScript/JavaScript
        "**/*.test.ts",
        "**/*.spec.ts",
        "**/*.test.js",
        "**/*.spec.js",
        # Python
        "**/test_*.py",
        "**/*_test.py",
        # Go
        "**/*_test.go",
        # Ruby
        "**/*_test.rb",
    ]

    def __init__(self, repo_path: Path, json_store: JSONStore):
        self.repo_path = repo_path
        self.json_store = json_store

    def run(self, repository_name: str) -> DiscoveryResult:
        """Execute discovery phase

        Args:
            repository_name: Name of the repository

        Returns:
            DiscoveryResult with all discovered test files
        """
        # Load previous discovery if exists
        previous_discovery = self._load_previous_discovery()

        # Find all test files
        discovered_files = self._find_test_files()

        # Build map of previous files for quick lookup
        previous_files_map = {}
        if previous_discovery:
            previous_files_map = {f["path"]: f for f in previous_discovery.get("test_files", [])}

        # Process discovered files and determine status
        test_files = []
        for file_path in discovered_files:
            sha256 = self._calculate_hash(file_path)
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

            # Determine status
            status = self._determine_status(
                str(file_path.relative_to(self.repo_path)), sha256, previous_files_map
            )

            test_files.append(
                TestFile(
                    path=str(file_path.relative_to(self.repo_path)),
                    sha256=sha256,
                    status=status,
                    last_modified=last_modified,
                )
            )

        # Check for deleted files
        if previous_files_map:
            current_paths = {str(f.relative_to(self.repo_path)) for f in discovered_files}
            for prev_path, prev_data in previous_files_map.items():
                if prev_path not in current_paths:
                    # File was deleted
                    test_files.append(
                        TestFile(
                            path=prev_path,
                            sha256=prev_data["sha256"],
                            status=FileStatus.DELETED,
                            last_modified=datetime.fromisoformat(
                                prev_data["last_modified"].replace("Z", "+00:00")
                            ),
                        )
                    )

        # Calculate summary statistics
        summary = self._calculate_summary(test_files, previous_discovery)

        # Create result
        result = DiscoveryResult(
            timestamp=datetime.now(),
            repository=repository_name,
            summary=summary,
            test_files=test_files,
        )

        # Save to JSON
        self.json_store.write_sync("01-discovery.json", result)

        return result

    def _find_test_files(self) -> list[Path]:
        """Find all test files matching patterns

        Returns:
            List of Path objects for test files
        """
        found_files = set()

        for pattern in self.TEST_PATTERNS:
            for file_path in self.repo_path.glob(pattern):
                if file_path.is_file():
                    found_files.add(file_path)

        return sorted(found_files)

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file

        Args:
            file_path: Path to file

        Returns:
            SHA-256 hash as hex string
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _determine_status(
        self, file_path: str, sha256: str, previous_files_map: dict
    ) -> FileStatus:
        """Determine the status of a file

        Args:
            file_path: Relative path to file
            sha256: Current SHA-256 hash
            previous_files_map: Map of previous files

        Returns:
            FileStatus enum value
        """
        if not previous_files_map:
            # First run - all files are created
            return FileStatus.CREATED

        if file_path not in previous_files_map:
            # New file
            return FileStatus.CREATED

        previous_file = previous_files_map[file_path]
        if previous_file["sha256"] != sha256:
            # File content changed
            return FileStatus.UPDATED

        # File unchanged
        return FileStatus.UNCHANGED

    def _calculate_summary(
        self, test_files: list[TestFile], previous_discovery: dict | None
    ) -> DiscoverySummary:
        """Calculate summary statistics

        Args:
            test_files: List of test files
            previous_discovery: Previous discovery data (if exists)

        Returns:
            DiscoverySummary with counts
        """
        status_counts = {
            FileStatus.CREATED: 0,
            FileStatus.UPDATED: 0,
            FileStatus.UNCHANGED: 0,
            FileStatus.DELETED: 0,
        }

        for test_file in test_files:
            status_counts[test_file.status] += 1

        total_files_discovered = sum(
            status_counts[status]
            for status in [FileStatus.CREATED, FileStatus.UPDATED, FileStatus.UNCHANGED]
        )

        total_files_tracked = len(test_files)

        return DiscoverySummary(
            total_files_discovered=total_files_discovered,
            total_files_tracked=total_files_tracked,
            created=status_counts[FileStatus.CREATED],
            updated=status_counts[FileStatus.UPDATED],
            unchanged=status_counts[FileStatus.UNCHANGED],
            deleted=status_counts[FileStatus.DELETED],
        )

    def _load_previous_discovery(self) -> dict | None:
        """Load previous discovery results if they exist

        Returns:
            Previous discovery data as dict, or None if doesn't exist
        """
        return self.json_store.read_optional_sync("01-discovery.json")
