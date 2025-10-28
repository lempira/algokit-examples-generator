"""Distillation node for Phase 3: Example Distillation"""

from datetime import datetime
from pathlib import Path

from ..agents.distillation import DistillationAgent
from ..models.phase_outputs import (
    DistillationResult,
    DistillationSummary,
    ExamplePlan,
    FileStatus,
)
from ..models.workflow import LLMConfig
from ..utils.json_store import JSONStore


class DistillationNode:
    """Phase 3: Plan example generation from test blocks"""

    def __init__(
        self,
        repo_path: Path,
        json_store: JSONStore,
        llm_config: LLMConfig,
        agent: DistillationAgent | None = None,
    ):
        self.repo_path = repo_path
        self.json_store = json_store
        self.llm_config = llm_config
        self.agent = agent if agent is not None else DistillationAgent(llm_config)

    def run(self, repository_name: str) -> DistillationResult:
        """Execute distillation phase

        Args:
            repository_name: Name of the repository

        Returns:
            DistillationResult with example plans
        """
        # Load extraction results
        extraction_data = self.json_store.read_sync("02-extraction.json")
        if not extraction_data:
            raise ValueError("Extraction results not found. Run extraction phase first.")

        # Load previous distillation if exists
        previous_distillation = self._load_previous_distillation()

        # Select high-quality test blocks
        selected_blocks = self._select_test_blocks(extraction_data)

        # Determine which examples to generate
        examples_to_plan = self._determine_examples_to_plan(
            selected_blocks, extraction_data, previous_distillation
        )

        # Plan examples using the agent
        planned_examples = []
        if examples_to_plan:
            planned_examples = self.agent.plan_examples_sync(
                test_blocks=examples_to_plan,
                repository_name=repository_name,
            )

        # Copy unchanged examples from previous run
        examples = self._merge_with_previous(
            planned_examples, previous_distillation, extraction_data
        )

        # Assign example IDs
        examples = self._assign_example_ids(examples)

        # Calculate summary
        summary = self._calculate_summary(examples)

        # Create result
        result = DistillationResult(
            timestamp=datetime.now(),
            repository=repository_name,
            examples=examples,
            summary=summary,
            refinement_history=[],
        )

        # Save to JSON
        self.json_store.write_sync("03-distillation.json", result)

        return result

    def _select_test_blocks(self, extraction_data: dict) -> list[dict]:
        """Select test blocks suitable for examples

        Args:
            extraction_data: Extraction results

        Returns:
            List of selected test blocks with metadata
        """
        selected = []

        for analysis in extraction_data.get("test_analysis", []):
            file_path = analysis["source_file"]
            file_status = analysis["file_status"]

            for block in analysis.get("test_blocks", []):
                # Filter by potential and classification
                if block["example_potential"] not in ["high", "medium"]:
                    continue

                if block["feature_classification"] not in ["user-facing", "mixed"]:
                    continue

                # Add metadata for planning
                block_with_meta = {
                    **block,
                    "source_file": file_path,
                    "file_status": file_status,
                }
                selected.append(block_with_meta)

        return selected

    def _determine_examples_to_plan(
        self,
        selected_blocks: list[dict],
        extraction_data: dict,
        previous_distillation: dict | None,
    ) -> list[dict]:
        """Determine which examples need planning

        Args:
            selected_blocks: Selected test blocks
            extraction_data: Extraction results
            previous_distillation: Previous distillation data (if exists)

        Returns:
            List of blocks that need planning
        """
        if not previous_distillation:
            # First run - plan all selected blocks
            return selected_blocks

        # Build set of files with changes
        changed_files = set()
        for analysis in extraction_data.get("test_analysis", []):
            file_status = analysis["file_status"]
            if file_status in [FileStatus.CREATED.value, FileStatus.UPDATED.value]:
                changed_files.add(analysis["source_file"])

        # Select blocks from changed files
        blocks_to_plan = [
            block for block in selected_blocks if block["source_file"] in changed_files
        ]

        return blocks_to_plan

    def _merge_with_previous(
        self,
        planned_examples: list[ExamplePlan],
        previous_distillation: dict | None,
        extraction_data: dict,
    ) -> list[ExamplePlan]:
        """Merge new plans with previous examples

        Args:
            planned_examples: Newly planned examples
            previous_distillation: Previous distillation data
            extraction_data: Extraction results

        Returns:
            Complete list of examples
        """
        if not previous_distillation:
            # Set all as planned
            for example in planned_examples:
                example.status = "planned"
            return planned_examples

        # Build set of deleted files
        deleted_files = set()
        for analysis in extraction_data.get("test_analysis", []):
            if analysis["file_status"] == FileStatus.DELETED.value:
                deleted_files.add(analysis["source_file"])

        # Get previous examples
        all_examples = []

        # Add new planned examples
        for example in planned_examples:
            example.status = "planned"
            all_examples.append(example)

        # Process previous examples
        for prev_example_data in previous_distillation.get("examples", []):
            # Check if source tests are deleted
            source_files = {st["file"] for st in prev_example_data.get("source_tests", [])}

            if source_files & deleted_files:
                # Mark for deletion
                prev_example = ExamplePlan.model_validate(prev_example_data)
                prev_example.status = "delete"
                all_examples.append(prev_example)
            else:
                # Check if already in new plans
                example_id = prev_example_data.get("example_id")
                if not any(e.example_id == example_id for e in planned_examples):
                    # Keep as-is
                    prev_example = ExamplePlan.model_validate(prev_example_data)
                    prev_example.status = "keep"
                    all_examples.append(prev_example)

        return all_examples

    def _assign_example_ids(self, examples: list[ExamplePlan]) -> list[ExamplePlan]:
        """Assign sequential IDs to examples

        Args:
            examples: List of examples

        Returns:
            Examples with assigned IDs and folders
        """
        # Group by complexity
        complexity_order = {"simple": 0, "moderate": 1, "complex": 2}

        # Sort by complexity, then alphabetically
        sorted_examples = sorted(
            examples,
            key=lambda e: (complexity_order.get(e.complexity, 3), e.title),
        )

        # Assign IDs
        for idx, example in enumerate(sorted_examples, start=1):
            # Generate ID from title
            title_slug = example.title.lower().replace(" ", "-")
            title_slug = "".join(c for c in title_slug if c.isalnum() or c == "-")
            example.example_id = f"{idx:02d}-{title_slug}"
            example.folder = f"examples/{example.example_id}"

        return sorted_examples

    def _calculate_summary(self, examples: list[ExamplePlan]) -> DistillationSummary:
        """Calculate summary statistics

        Args:
            examples: List of examples

        Returns:
            DistillationSummary
        """
        planned = sum(1 for e in examples if e.status == "planned")
        keep = sum(1 for e in examples if e.status == "keep")
        delete = sum(1 for e in examples if e.status == "delete")

        complexity_breakdown = {"simple": 0, "moderate": 0, "complex": 0}
        for example in examples:
            complexity_breakdown[example.complexity] += 1

        return DistillationSummary(
            total_examples=len(examples),
            planned=planned,
            keep=keep,
            delete=delete,
            complexity_breakdown=complexity_breakdown,
        )

    def _load_previous_distillation(self) -> dict | None:
        """Load previous distillation results if they exist

        Returns:
            Previous distillation data as dict, or None if doesn't exist
        """
        return self.json_store.read_optional_sync("03-distillation.json")
