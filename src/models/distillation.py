"""Pydantic models for Distillation phase (Phase 3)"""

from datetime import datetime

from pydantic import BaseModel, Field


class EnvironmentVariable(BaseModel):
    """Environment variable requirement"""

    name: str = ""
    required: bool = True
    example: str = ""


class ExamplePrerequisites(BaseModel):
    """Prerequisites for running an example"""

    tools: list[str] = Field(default_factory=list)
    libraries: list[str] = Field(default_factory=list)
    environment: list[EnvironmentVariable] = Field(default_factory=list)


class RunInstructions(BaseModel):
    """Instructions for running an example"""

    setup: list[str] = Field(default_factory=list)
    install: list[str] = Field(default_factory=list)
    execute: list[str] = Field(default_factory=list)


class SourceTest(BaseModel):
    """Reference to source test"""

    file: str = ""
    test_name: str = ""


class ArtifactPlan(BaseModel):
    """Plan for handling an artifact"""

    target_file: str = ""
    type: str = "file"  # "contract", "config", "data", etc.
    action: str = "copy"  # "copy" or "generate"
    source_path: str | None = None
    note: str = ""


class ExamplePlan(BaseModel):
    """Plan for generating a single example"""

    example_id: str = ""  # Assigned by distillation node
    title: str = "Untitled Example"
    summary: str = ""
    language: str = "unknown"
    complexity: str = "unknown"  # "simple", "moderate", or "complex"
    example_potential: str = "unknown"  # "high" or "medium"
    use_case_category: str = ""
    specific_use_case: str = ""
    target_users: list[str] = Field(default_factory=list)
    features_tested: list[str] = Field(default_factory=list)
    feature_tags: list[str] = Field(default_factory=list)
    folder: str = ""  # Assigned by distillation node
    prerequisites: ExamplePrerequisites = Field(default_factory=ExamplePrerequisites)
    run_instructions: RunInstructions = Field(default_factory=RunInstructions)
    expected_output: list[str] = Field(default_factory=list)
    source_tests: list[SourceTest] = Field(default_factory=list)
    artifacts_plan: list[ArtifactPlan] = Field(default_factory=list)
    notes: str = ""


class DistillationSummary(BaseModel):
    """Summary statistics for distillation phase"""

    total_examples: int = 0
    complexity_breakdown: dict[str, int] = Field(
        default_factory=dict
    )  # "simple", "moderate", "complex"


class RefinementHistoryEntry(BaseModel):
    """Entry in refinement history"""

    iteration: int = 1
    timestamp: datetime | None = None
    changes_applied: int = 0
    issues_resolved: list[str] = Field(default_factory=list)
    examples_updated: list[str] = Field(default_factory=list)
    issues_before: int = 0
    issues_after: int = 0


class DistillationResult(BaseModel):
    """Output from Phase 3: Distillation"""

    timestamp: datetime | None = None
    repository: str = ""
    examples: list[ExamplePlan] = Field(default_factory=list)
    summary: DistillationSummary = Field(default_factory=DistillationSummary)
    refinement_history: list[RefinementHistoryEntry] = Field(default_factory=list)

    def get_plan(self, example_id: str) -> ExamplePlan | None:
        """Get a specific example plan by ID"""
        return next((p for p in self.examples if p.example_id == example_id), None)
