"""Distillation node for Phase 3: Example Distillation"""

from datetime import datetime
from pathlib import Path

from ..agents.distillation import DistillationAgent
from ..models import DistillationResult, DistillationSummary, ExamplePlan, LLMConfig
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
        print("\n=== Phase 3: Distillation ===")
        print(f"Repository: {repository_name}")

        # Load extraction results
        print("\nLoading extraction results...")
        extraction_data = self.json_store.read_sync("02-extraction.json")
        if not extraction_data:
            raise ValueError("Extraction results not found. Run extraction phase first.")

        total_blocks = sum(
            len(analysis.get("test_blocks", []))
            for analysis in extraction_data.get("test_analysis", [])
        )
        print(f"Found {total_blocks} total test blocks from extraction")

        # Select high-quality test blocks
        print("\nFiltering test blocks for example generation...")
        selected_blocks = self._select_test_blocks(extraction_data)
        print(f"Selected {len(selected_blocks)} test blocks for planning")
        print(
            "  (Filtered by: example_potential=['high','medium'] + feature_classification=['user-facing','mixed'])"
        )

        # Plan all examples using the agent
        examples = []
        if selected_blocks:
            print("\nPlanning examples with LLM agent...")
            examples = self.agent.plan_examples_sync(
                test_blocks=selected_blocks,
                repository_name=repository_name,
            )
        else:
            print("\n⚠️  No test blocks selected - no examples will be planned")

        # Assign example IDs
        if examples:
            print("\nAssigning example IDs and folders...")
            examples = self._assign_example_ids(examples)
            print(f"Assigned IDs to {len(examples)} examples")

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

        print("\n✅ Distillation complete:")
        print(f"   Total examples planned: {summary.total_examples}")
        print("   Complexity breakdown:")
        print(f"     - Simple: {summary.complexity_breakdown.get('simple', 0)}")
        print(f"     - Moderate: {summary.complexity_breakdown.get('moderate', 0)}")
        print(f"     - Complex: {summary.complexity_breakdown.get('complex', 0)}")

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

            for block in analysis.get("test_blocks", []):
                # Filter by potential and classification
                if block.get("example_potential") not in ["high", "medium"]:
                    continue

                if block.get("feature_classification") not in ["user-facing", "mixed"]:
                    continue

                # Add metadata for planning
                block_with_meta = {
                    **block,
                    "source_file": file_path,
                }
                selected.append(block_with_meta)

        return selected

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
        print("  Generating example IDs (sorted by complexity):")
        for idx, example in enumerate(sorted_examples, start=1):
            # Generate ID from title
            title_slug = example.title.lower().replace(" ", "-")
            title_slug = "".join(c for c in title_slug if c.isalnum() or c == "-")
            example.example_id = f"{idx:02d}-{title_slug}"
            example.folder = example.example_id  # Just the ID, no "examples/" prefix

            complexity_emoji = {"simple": "🟢", "moderate": "🟡", "complex": "🔴"}.get(
                example.complexity, "⚪"
            )
            if idx <= 10:  # Show first 10
                print(f"    {complexity_emoji} {example.example_id}")

        if len(sorted_examples) > 10:
            print(f"    ... and {len(sorted_examples) - 10} more")

        return sorted_examples

    def _calculate_summary(self, examples: list[ExamplePlan]) -> DistillationSummary:
        """Calculate summary statistics

        Args:
            examples: List of examples

        Returns:
            DistillationSummary
        """
        complexity_breakdown = {"simple": 0, "moderate": 0, "complex": 0}
        for example in examples:
            complexity_breakdown[example.complexity] += 1

        return DistillationSummary(
            total_examples=len(examples),
            complexity_breakdown=complexity_breakdown,
        )
