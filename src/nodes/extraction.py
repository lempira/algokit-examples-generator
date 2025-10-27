"""Extraction node for Phase 2: Test Block Extraction"""

from datetime import datetime
from pathlib import Path

from ..agents.extraction import ExtractionAgent
from ..models.phase_outputs import (
    ExtractionResult,
    ExtractionSummary,
    FileStatus,
    TestFileAnalysis,
)
from ..models.workflow import LLMConfig
from ..utils.file_reader import CodeFileReader
from ..utils.json_store import JSONStore


class ExtractionNode:
    """Phase 2: Extract test blocks from test files"""

    def __init__(
        self,
        repo_path: Path,
        json_store: JSONStore,
        file_reader: CodeFileReader,
        llm_config: LLMConfig,
        agent: ExtractionAgent | None = None,
    ):
        self.repo_path = repo_path
        self.json_store = json_store
        self.file_reader = file_reader
        self.llm_config = llm_config
        self.agent = agent if agent is not None else ExtractionAgent(llm_config)

    def run(self, repository_name: str) -> ExtractionResult:
        """Execute extraction phase

        Args:
            repository_name: Name of the repository

        Returns:
            ExtractionResult with analyzed test blocks
        """
        # Load discovery results
        discovery_data = self.json_store.read_sync("01-discovery.json")
        if not discovery_data:
            raise ValueError("Discovery results not found. Run discovery phase first.")

        # Load previous extraction if exists
        previous_extraction = self._load_previous_extraction()

        # Determine which files to parse
        test_files = discovery_data.get("test_files", [])
        files_to_parse, files_to_copy, files_to_mark_deleted = self._categorize_files(
            test_files, previous_extraction
        )

        # Parse and analyze files
        test_analysis = []

        # Parse new/updated files
        for test_file_data in files_to_parse:
            file_path = test_file_data["path"]
            file_status = test_file_data["status"]

            try:
                # Read file content
                file_content = self.file_reader.read_sync(file_path)

                # Analyze with agent
                analysis = self.agent.analyze_test_file_sync(
                    file_path=file_path,
                    file_content=file_content,
                    repository_name=repository_name,
                )

                # Update file status
                analysis.file_status = file_status

                test_analysis.append(analysis)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue

        # Copy unchanged files
        test_analysis.extend(files_to_copy)

        # Mark deleted files
        test_analysis.extend(files_to_mark_deleted)

        # Calculate summary
        summary = self._calculate_summary(test_analysis, test_files)

        # Create result
        result = ExtractionResult(
            timestamp=datetime.now(),
            repository=repository_name,
            summary=summary,
            test_analysis=test_analysis,
        )

        # Save to JSON
        self.json_store.write_sync("02-extraction.json", result)

        return result

    def _categorize_files(
        self,
        test_files: list[dict],
        previous_extraction: dict | None,
    ) -> tuple[list[dict], list[TestFileAnalysis], list[TestFileAnalysis]]:
        """Categorize files into parse, copy, or mark deleted

        Args:
            test_files: List of test files from discovery
            previous_extraction: Previous extraction data (if exists)

        Returns:
            Tuple of (files_to_parse, files_to_copy, files_to_mark_deleted)
        """
        if not previous_extraction:
            # First run - parse all files
            return (test_files, [], [])

        # Build map of previous analyses
        previous_analyses = {
            analysis["source_file"]: analysis
            for analysis in previous_extraction.get("test_analysis", [])
        }

        files_to_parse = []
        files_to_copy = []
        files_to_mark_deleted = []

        # Categorize current files
        for test_file in test_files:
            file_path = test_file["path"]
            file_status = test_file["status"]

            if file_status in [FileStatus.CREATED.value, FileStatus.UPDATED.value]:
                # Parse new/updated files
                files_to_parse.append(test_file)
            elif file_status == FileStatus.UNCHANGED.value:
                # Copy unchanged files from previous extraction
                if file_path in previous_analyses:
                    prev_analysis = previous_analyses[file_path]
                    from ..models.phase_outputs import TestBlock

                    files_to_copy.append(
                        TestFileAnalysis(
                            source_file=prev_analysis["source_file"],
                            file_status=FileStatus.UNCHANGED.value,
                            test_blocks=[
                                TestBlock.model_validate(block)
                                for block in prev_analysis.get("test_blocks", [])
                            ],
                        )
                    )
            elif file_status == FileStatus.DELETED.value:
                # Mark deleted files
                if file_path in previous_analyses:
                    from ..models.phase_outputs import TestBlock

                    prev_analysis = previous_analyses[file_path]
                    files_to_mark_deleted.append(
                        TestFileAnalysis(
                            source_file=prev_analysis["source_file"],
                            file_status=FileStatus.DELETED.value,
                            test_blocks=[
                                TestBlock.model_validate(block)
                                for block in prev_analysis.get("test_blocks", [])
                            ],
                        )
                    )

        return (files_to_parse, files_to_copy, files_to_mark_deleted)

    def _calculate_summary(
        self,
        test_analysis: list[TestFileAnalysis],
        test_files: list[dict],
    ) -> ExtractionSummary:
        """Calculate summary statistics

        Args:
            test_analysis: List of test file analyses
            test_files: List of test files from discovery

        Returns:
            ExtractionSummary with counts
        """
        # Count test blocks by file status
        from_created = 0
        from_updated = 0
        from_unchanged = 0
        from_deleted = 0

        # Count by potential and complexity
        potential_breakdown = {"high": 0, "medium": 0, "low": 0}
        complexity_breakdown = {"simple": 0, "moderate": 0, "complex": 0}

        for analysis in test_analysis:
            # Count by file status
            block_count = len(analysis.test_blocks)
            if analysis.file_status == FileStatus.CREATED.value:
                from_created += block_count
            elif analysis.file_status == FileStatus.UPDATED.value:
                from_updated += block_count
            elif analysis.file_status == FileStatus.UNCHANGED.value:
                from_unchanged += block_count
            elif analysis.file_status == FileStatus.DELETED.value:
                from_deleted += block_count

            # Count by potential and complexity
            for block in analysis.test_blocks:
                potential_breakdown[block.example_potential] += 1
                complexity_breakdown[block.complexity] += 1

        total_test_blocks = from_created + from_updated + from_unchanged + from_deleted

        return ExtractionSummary(
            total_test_blocks=total_test_blocks,
            from_created_files=from_created,
            from_updated_files=from_updated,
            from_unchanged_files=from_unchanged,
            from_deleted_files=from_deleted,
            potential_breakdown=potential_breakdown,
            complexity_breakdown=complexity_breakdown,
        )

    def _load_previous_extraction(self) -> dict | None:
        """Load previous extraction results if they exist

        Returns:
            Previous extraction data as dict, or None if doesn't exist
        """
        return self.json_store.read_optional_sync("02-extraction.json")
