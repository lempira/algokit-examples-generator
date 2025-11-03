"""Main workflow orchestration using pydantic-graph"""

from pathlib import Path

from .config import settings
from .models.workflow import LLMConfig, WorkflowDeps, WorkflowState
from .nodes import (
    DiscoveryNode,
    DistillationNode,
    ExtractionNode,
    GenerationNode,
    QualityNode,
    RefinementNode,
)
from .utils.code_executor import CodeExecutor
from .utils.file_reader import CodeFileReader
from .utils.json_store import JSONStore


class ExampleGenerationWorkflow:
    """Orchestrates the complete test-to-example extraction workflow"""

    def __init__(self, deps: WorkflowDeps, max_refinement_iterations: int = 3):
        """Initialize workflow with dependencies

        Args:
            deps: Workflow dependencies (paths, utilities, config)
            max_refinement_iterations: Maximum number of refinement iterations
        """
        self.deps = deps
        self.state = WorkflowState(max_refinement_iterations=max_refinement_iterations)

    def run(self, repository_name: str) -> WorkflowState:
        """Execute the complete workflow

        Args:
            repository_name: Name of the repository

        Returns:
            Final workflow state
        """
        print("=" * 60)
        print("Test-to-Example Extraction Workflow")
        print("=" * 60)

        # Phase 1: Discovery
        print("\n[Phase 1/6] Discovery - Scanning test files...")
        discovery_result = self._run_discovery(repository_name)
        self.state.discovery_data = discovery_result
        print(f"✓ Found {discovery_result.summary.total_files} test files")

        # Phase 2: Extraction
        print("\n[Phase 2/6] Extraction - Analyzing test blocks...")
        extraction_result = self._run_extraction(repository_name)
        self.state.extraction_data = extraction_result
        print(f"✓ Extracted {extraction_result.summary.total_test_blocks} test blocks")

        # Phase 3: Distillation
        print("\n[Phase 3/6] Distillation - Planning examples...")
        distillation_result = self._run_distillation(repository_name)
        self.state.distillation_data = distillation_result
        print(f"✓ Planned {distillation_result.summary.total_examples} examples")

        # Phase 4: Generation
        print("\n[Phase 4/6] Generation - Creating example files...")
        generation_result = self._run_generation(repository_name)
        self.state.generation_data = generation_result
        print(f"✓ Generated {generation_result.summary.generated} examples")

        # Phase 5 & 6: Quality → Refinement loop (max 3 iterations)
        print("\n[Phase 5/6] Quality Assurance - Validating examples...")
        for iteration in range(1, self.state.max_refinement_iterations + 1):
            self.state.refinement_iteration = iteration

            quality_result = self._run_quality(repository_name, iteration)
            self.state.quality_data = quality_result

            print(
                f"\n  Iteration {iteration}: Found {quality_result.severity_summary.total} issues "
                f"({quality_result.severity_summary.critical} critical, "
                f"{quality_result.severity_summary.high} high)"
            )

            if not quality_result.should_trigger_refinement:
                print(f"  ✓ Quality check passed! {quality_result.refinement_reason}")
                break

            if iteration >= self.state.max_refinement_iterations:
                print(
                    f"  ⚠ Max refinement iterations ({self.state.max_refinement_iterations}) reached"
                )
                break

            # Phase 6: Refinement
            print(f"\n[Phase 6/6] Refinement - Fixing issues (iteration {iteration})...")
            refinement_result = self._run_refinement(repository_name, iteration)

            print(
                f"  ✓ Applied {refinement_result.changes_applied} fixes to "
                f"{len(refinement_result.examples_updated)} examples"
            )

            # Loop back to quality check
            print("\n  Re-running quality checks...")

        # Final summary
        print("\n" + "=" * 60)
        print("Workflow Complete!")
        print("=" * 60)
        if self.state.quality_data:
            print(
                f"Final Status: {self.state.quality_data.validation_results.passed}/"
                f"{self.state.quality_data.validation_results.examples_validated} examples passed"
            )
            print(
                f"Total Issues: {self.state.quality_data.severity_summary.total} "
                f"({self.state.quality_data.severity_summary.critical} critical, "
                f"{self.state.quality_data.severity_summary.high} high, "
                f"{self.state.quality_data.severity_summary.medium} medium, "
                f"{self.state.quality_data.severity_summary.low} low)"
            )

        print(f"\nOutput files saved to: {self.deps.examples_output_path}")
        print("=" * 60)

        return self.state

    def _run_discovery(self, repository_name: str):
        """Run Phase 1: Discovery"""
        node = DiscoveryNode(
            repo_path=self.deps.repo_path,
            json_store=self.deps.json_store,
            discovery_paths=settings.get_discovery_paths(),
        )
        return node.run(repository_name)

    def _run_extraction(self, repository_name: str):
        """Run Phase 2: Extraction"""
        node = ExtractionNode(
            repo_path=self.deps.repo_path,
            json_store=self.deps.json_store,
            file_reader=self.deps.file_reader,
            llm_config=self.deps.llm_config,
        )
        return node.run(repository_name)

    def _run_distillation(self, repository_name: str):
        """Run Phase 3: Distillation"""
        node = DistillationNode(
            repo_path=self.deps.repo_path,
            json_store=self.deps.json_store,
            llm_config=self.deps.llm_config,
        )
        return node.run(repository_name)

    def _run_generation(self, repository_name: str):
        """Run Phase 4: Generation"""
        node = GenerationNode(
            repo_path=self.deps.repo_path,
            examples_path=self.deps.examples_output_path,
            json_store=self.deps.json_store,
            file_reader=self.deps.file_reader,
            llm_config=self.deps.llm_config,
        )
        return node.run(repository_name)

    def _run_quality(self, repository_name: str, iteration: int):
        """Run Phase 5: Quality"""
        node = QualityNode(
            repo_path=self.deps.repo_path,
            examples_path=self.deps.examples_output_path,
            json_store=self.deps.json_store,
            executor=self.deps.executor,
            llm_config=self.deps.llm_config,
            iteration=iteration,
        )
        return node.run(repository_name)

    def _run_refinement(self, repository_name: str, iteration: int):
        """Run Phase 6: Refinement"""
        node = RefinementNode(
            repo_path=self.deps.repo_path,
            examples_path=self.deps.examples_output_path,
            json_store=self.deps.json_store,
            llm_config=self.deps.llm_config,
            iteration=iteration,
        )
        return node.run(repository_name)


def create_workflow(
    repo_path: Path,
    examples_output_path: Path | None = None,
    llm_model: str | None = None,
    temperature: float = 0.7,
    max_refinement_iterations: int = 3,
) -> ExampleGenerationWorkflow:
    """Create a workflow instance with default dependencies

    Args:
        repo_path: Path to the repository
        examples_output_path: Path for example outputs (default: repo_path/examples)
        llm_model: LLM model to use (default: claude-3-5-sonnet-20241022)
        temperature: LLM temperature setting (default: 0.7)
        max_refinement_iterations: Maximum refinement iterations (default: 3)

    Returns:
        Configured ExampleGenerationWorkflow
    """
    if examples_output_path is None:
        examples_output_path = repo_path / "examples"

    # Ensure examples directory exists
    examples_output_path.mkdir(parents=True, exist_ok=True)

    # Create dependencies
    deps = WorkflowDeps(
        repo_path=repo_path,
        examples_output_path=examples_output_path,
        file_reader=CodeFileReader(repo_path),
        json_store=JSONStore(examples_output_path),
        executor=CodeExecutor(),
        llm_config=LLMConfig(
            default_model=llm_model or "anthropic:claude-3-5-sonnet-20241022",
            temperature=temperature,
        ),
    )

    return ExampleGenerationWorkflow(deps, max_refinement_iterations)
