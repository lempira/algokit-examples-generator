"""Phase 1: Discovery Node - Find and track test files"""

from datetime import datetime
from pathlib import Path

from ..models import DiscoveryResult, DiscoverySummary, TestFile
from ..utils.json_store import JSONStore


class DiscoveryNode:
    """Phase 1: Discover test files"""

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
    ]

    def __init__(
        self,
        repo_path: Path,
        json_store: JSONStore,
        discovery_paths: list[str] | None = None,
        filter_files: list[str] | None = None,
    ):
        self.repo_path = repo_path
        self.json_store = json_store
        self.discovery_paths = discovery_paths or ["src"]
        self.filter_files = filter_files

    def run(self, repository_name: str) -> DiscoveryResult:
        """Execute discovery phase

        Args:
            repository_name: Name of the repository

        Returns:
            DiscoveryResult with all discovered test files
        """
        print("\n=== Phase 1: Discovery ===")
        print(f"Repository: {repository_name}")

        # Find all test files
        discovered_files = self._find_test_files()
        print(f"Found {len(discovered_files)} test files")

        # Convert to TestFile objects
        test_files = self._process_files(discovered_files)

        # Calculate summary statistics
        summary = self._calculate_summary(test_files)

        # Create result
        result = DiscoveryResult(
            timestamp=datetime.now(),
            repository=repository_name,
            summary=summary,
            test_files=test_files,
        )

        # Save to JSON
        self.json_store.write_sync("01-discovery.json", result)

        print("\n✅ Discovery complete:")
        print(f"   Files: {summary.total_files}")

        return result

    def _process_files(self, discovered_files: list[Path]) -> list[TestFile]:
        """Convert discovered file paths to TestFile objects

        Args:
            discovered_files: List of discovered file paths

        Returns:
            List of TestFile objects
        """
        test_files = []

        for file_path in discovered_files:
            rel_path = str(file_path.relative_to(self.repo_path))
            last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

            test_files.append(
                TestFile(
                    path=rel_path,
                    last_modified=last_modified,
                )
            )

        return test_files

    def _find_test_files(self) -> list[Path]:
        """Find all test files matching patterns in specified discovery paths

        Returns:
            List of Path objects for test files
        """
        found_files = set()

        # If specific files are requested, only find those
        if self.filter_files:
            for file_name in self.filter_files:
                file_path = self.repo_path / file_name
                if file_path.exists() and file_path.is_file():
                    found_files.add(file_path)
                else:
                    print(f"  Warning: Requested file not found: {file_name}")
            return sorted(found_files)

        # Otherwise, search within specified subdirectories
        for search_path in self.discovery_paths:
            base_path = self.repo_path / search_path
            if not base_path.exists():
                continue  # Skip if path doesn't exist

            for pattern in self.TEST_PATTERNS:
                for file_path in base_path.glob(pattern):
                    if file_path.is_file():
                        found_files.add(file_path)

        return sorted(found_files)

    def _calculate_summary(self, test_files: list[TestFile]) -> DiscoverySummary:
        """Calculate summary statistics

        Args:
            test_files: List of test files

        Returns:
            DiscoverySummary with counts
        """
        return DiscoverySummary(
            total_files=len(test_files),
        )
