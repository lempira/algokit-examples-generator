"""Extraction node for Phase 2: Test Block Extraction"""

import asyncio
from datetime import datetime
from pathlib import Path

from ..agents import extraction
from ..models import ExtractionResult, ExtractionSummary, LLMConfig, TestFileAnalysis
from ..utils.file_reader import CodeFileReader
from ..utils.json_store import JSONStore

# Configuration: Number of files to process concurrently per batch
BATCH_SIZE = 3


class ExtractionNode:
    """Phase 2: Extract test blocks from test files"""

    def __init__(
        self,
        repo_path: Path,
        json_store: JSONStore,
        file_reader: CodeFileReader,
        llm_config: LLMConfig,
    ):
        self.repo_path = repo_path
        self.json_store = json_store
        self.file_reader = file_reader
        self.llm_config = llm_config
        # Create the agent once and reuse it
        self.agent = extraction.create_extraction_agent(llm_config)

    def run(self, repository_name: str) -> ExtractionResult:
        """Execute extraction phase - Analyze test files

        Args:
            repository_name: Name of the repository

        Returns:
            ExtractionResult with extracted test blocks
        """
        print("\n=== Phase 2: Extraction ===")

        # Load discovery results
        from ..models import DiscoveryResult

        discovery_data_raw = self.json_store.read_sync("01-discovery.json")
        if not discovery_data_raw:
            raise ValueError("Discovery results not found. Run discovery phase first.")

        discovery_result = DiscoveryResult.model_validate(discovery_data_raw)

        print(f"Analyzing {len(discovery_result.test_files)} test files")

        # Process files in batches using async
        test_analysis = asyncio.run(
            self._process_batches(discovery_result.test_files, repository_name)
        )

        # Calculate summary
        summary = self._calculate_summary(test_analysis)

        # Create result
        result = ExtractionResult(
            timestamp=datetime.now(),
            repository=repository_name,
            summary=summary,
            test_analysis=test_analysis,
        )

        # Save to JSON
        self.json_store.write_sync("02-extraction.json", result)

        print("\n✅ Extraction complete:")
        print(f"   Test blocks extracted: {summary.total_test_blocks}")

        return result

    async def _process_batches(
        self, test_files: list, repository_name: str
    ) -> list[TestFileAnalysis]:
        """Process test files in batches for better performance

        Args:
            test_files: List of TestFile objects from discovery
            repository_name: Name of the repository

        Returns:
            List of TestFileAnalysis
        """
        all_analyses = []

        # Process files in batches
        for i in range(0, len(test_files), BATCH_SIZE):
            batch = test_files[i : i + BATCH_SIZE]
            print(f"\nProcessing batch {i // BATCH_SIZE + 1} ({len(batch)} files):")

            # Process batch concurrently
            batch_tasks = [self._analyze_file(tf.path, repository_name) for tf in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Collect results
            for test_file, result in zip(batch, batch_results, strict=True):
                if isinstance(result, Exception):
                    print(f"  ❌ {test_file.path}: Error - {result}")
                    all_analyses.append(
                        TestFileAnalysis(source_file=test_file.path, test_blocks=[])
                    )
                else:
                    blocks_found = len(result.test_blocks)
                    print(f"  ✅ {test_file.path}: {blocks_found} test blocks")
                    all_analyses.append(result)

        return all_analyses

    async def _analyze_file(self, file_path: str, repository_name: str) -> TestFileAnalysis:
        """Analyze a single test file

        Args:
            file_path: Path to test file
            repository_name: Repository name

        Returns:
            TestFileAnalysis
        """
        # Read file content (async)
        file_content = await self.file_reader.read(file_path)

        # Analyze with agent
        return await extraction.analyze_test_file(
            self.agent, file_path, file_content, repository_name
        )

    def _calculate_summary(self, test_analysis: list[TestFileAnalysis]) -> ExtractionSummary:
        """Calculate summary statistics

        Args:
            test_analysis: List of test file analyses

        Returns:
            ExtractionSummary with counts
        """
        total_blocks = 0
        for analysis in test_analysis:
            total_blocks += len(analysis.test_blocks)

        return ExtractionSummary(total_test_blocks=total_blocks)
