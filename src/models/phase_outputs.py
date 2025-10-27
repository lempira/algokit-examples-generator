"""Pydantic models for all phase outputs"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# Phase 1: Discovery Models
class FileStatus(str, Enum):
    """Status of a test file"""
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


class TestFile(BaseModel):
    """Represents a discovered test file"""
    path: str
    sha256: str
    status: FileStatus
    last_modified: datetime


class DiscoverySummary(BaseModel):
    """Summary statistics for discovery phase"""
    total_files_discovered: int
    total_files_tracked: int
    created: int
    updated: int
    unchanged: int
    deleted: int


class DiscoveryResult(BaseModel):
    """Output from Phase 1: Discovery"""
    timestamp: datetime
    repository: str
    summary: DiscoverySummary
    test_files: list[TestFile]

    def get_file(self, file_path: str) -> TestFile | None:
        """Get a test file by path"""
        return next((f for f in self.test_files if f.path == file_path), None)

    def get_changed_files(self) -> list[str]:
        """Get list of file paths that have changed"""
        return [
            f.path
            for f in self.test_files
            if f.status in [FileStatus.CREATED, FileStatus.UPDATED]
        ]


# Phase 2: Extraction Models
class Prerequisites(BaseModel):
    """Prerequisites for running a test block"""
    imports: list[str]
    setup_requirements: list[str]
    configuration: list[str]


class TestBlock(BaseModel):
    """Represents an extracted test block"""
    test_name: str
    line_range: str  # e.g., "45-78"
    features_tested: list[str]
    feature_classification: str  # "user-facing", "internal", or "mixed"
    use_case_category: str | None = None  # Only if user-facing or mixed
    specific_use_case: str | None = None  # Only if user-facing or mixed
    target_users: list[str] = Field(default_factory=list)  # Only if user-facing or mixed
    example_potential: str  # "high", "medium", or "low"
    complexity: str  # "simple", "moderate", or "complex"
    prerequisites: Prerequisites
    key_concepts: list[str]
    user_value: str | None = None  # Only if user-facing or mixed


class TestFileAnalysis(BaseModel):
    """Analysis of a single test file"""
    source_file: str
    file_status: FileStatus
    test_blocks: list[TestBlock]


class ExtractionSummary(BaseModel):
    """Summary statistics for extraction phase"""
    total_test_blocks: int
    from_created_files: int
    from_updated_files: int
    from_unchanged_files: int
    from_deleted_files: int
    potential_breakdown: dict[str, int]  # "high", "medium", "low"
    complexity_breakdown: dict[str, int]  # "simple", "moderate", "complex"


class ExtractionResult(BaseModel):
    """Output from Phase 2: Extraction"""
    timestamp: datetime
    repository: str
    summary: ExtractionSummary
    test_analysis: list[TestFileAnalysis]

    def get_blocks_for_file(self, file_path: str) -> list[TestBlock]:
        """Get all blocks from a specific file"""
        for analysis in self.test_analysis:
            if analysis.source_file == file_path:
                return analysis.test_blocks
        return []

    def get_high_potential_blocks(self) -> list[TestBlock]:
        """Get blocks with high example potential"""
        blocks = []
        for analysis in self.test_analysis:
            blocks.extend([b for b in analysis.test_blocks if b.example_potential == "high"])
        return blocks


# Phase 3: Distillation Models
class EnvironmentVariable(BaseModel):
    """Environment variable requirement"""
    name: str
    required: bool
    example: str


class ExamplePrerequisites(BaseModel):
    """Prerequisites for running an example"""
    tools: list[str]
    libraries: list[str]
    environment: list[EnvironmentVariable] = Field(default_factory=list)


class RunInstructions(BaseModel):
    """Instructions for running an example"""
    setup: list[str] = Field(default_factory=list)
    install: list[str]
    execute: list[str]


class SourceTest(BaseModel):
    """Reference to source test"""
    file: str
    test_name: str


class ArtifactPlan(BaseModel):
    """Plan for handling an artifact"""
    target_file: str
    type: str  # "contract", "config", "data", etc.
    action: str  # "copy" or "generate"
    source_path: str | None = None
    note: str = ""


class ExamplePlan(BaseModel):
    """Plan for generating a single example"""
    example_id: str
    title: str
    summary: str
    language: str
    complexity: str  # "simple", "moderate", or "complex"
    example_potential: str  # "high" or "medium"
    use_case_category: str
    specific_use_case: str
    target_users: list[str]
    features_tested: list[str]
    feature_tags: list[str]
    folder: str
    prerequisites: ExamplePrerequisites
    run_instructions: RunInstructions
    expected_output: list[str]
    source_tests: list[SourceTest]
    artifacts_plan: list[ArtifactPlan]
    status: str  # "planned", "keep", or "delete"
    notes: str = ""


class DistillationSummary(BaseModel):
    """Summary statistics for distillation phase"""
    total_examples: int
    planned: int
    keep: int
    delete: int
    complexity_breakdown: dict[str, int]  # "simple", "moderate", "complex"


class RefinementHistoryEntry(BaseModel):
    """Entry in refinement history"""
    iteration: int
    timestamp: datetime
    changes_applied: int
    issues_resolved: list[str]
    examples_updated: list[str]
    issues_before: int = 0
    issues_after: int = 0


class DistillationResult(BaseModel):
    """Output from Phase 3: Distillation"""
    timestamp: datetime
    repository: str
    examples: list[ExamplePlan]
    summary: DistillationSummary
    refinement_history: list[RefinementHistoryEntry] = Field(default_factory=list)

    def get_plan(self, example_id: str) -> ExamplePlan | None:
        """Get a specific example plan by ID"""
        return next((p for p in self.examples if p.example_id == example_id), None)


# Phase 4: Generation Models
class GeneratedArtifact(BaseModel):
    """Generated artifact information"""
    target_file: str
    source: str  # "copied" or "generated"
    source_path: str | None = None


class GeneratedExample(BaseModel):
    """Represents a generated example"""
    example_id: str
    title: str
    folder: str
    status: str  # "generated", "needs_review", or "error"
    generated_files: list[str]
    generated_artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    generation_notes: str = ""
    source_tests: list[SourceTest]


class GenerationSummary(BaseModel):
    """Summary statistics for generation phase"""
    total_examples: int
    generated: int
    needs_review: int
    error: int
    kept_unchanged: int
    deleted: int


class GenerationResult(BaseModel):
    """Output from Phase 4: Generation"""
    timestamp: datetime
    repository: str
    examples: list[GeneratedExample]
    summary: GenerationSummary
    refinement_history: list[RefinementHistoryEntry] = Field(default_factory=list)

    def get_example(self, example_id: str) -> GeneratedExample | None:
        """Get a specific generated example by ID"""
        return next(
            (e for e in self.examples if e.example_id == example_id),
            None
        )

    def get_successful_examples(self) -> list[GeneratedExample]:
        """Get all successfully generated examples"""
        return [e for e in self.examples if e.status == "generated"]


# Phase 5: Quality Models
class ValidationCheckResult(BaseModel):
    """Result of a specific validation check"""
    passed: int
    checks: list[str]
    language: str | None = None  # For language_compliance check


class ValidationChecks(BaseModel):
    """All validation checks performed"""
    completeness: ValidationCheckResult
    api_usage: ValidationCheckResult
    language_compliance: ValidationCheckResult
    artifacts: ValidationCheckResult


class QualityIssue(BaseModel):
    """Represents a quality issue found in an example"""
    type: str  # e.g., "missing_env_var", "type_error", "import_error"
    severity: str  # "critical", "high", "medium", or "low"
    description: str
    recommendation: str
    check: str | None = None  # Which check found this issue


class ExampleIssues(BaseModel):
    """Issues found for a specific example"""
    example_id: str
    issues: list[QualityIssue]


class ValidationResults(BaseModel):
    """Detailed validation results"""
    examples_validated: int
    passed: int
    failed: int
    validation_checks: ValidationChecks
    issues_by_example: list[ExampleIssues]


class SeveritySummary(BaseModel):
    """Summary of issues by severity"""
    critical: int
    high: int
    medium: int
    low: int
    total: int


class QualityResult(BaseModel):
    """Output from Phase 5: Quality"""
    timestamp: datetime
    repository: str
    iteration: int
    validation_results: ValidationResults
    severity_summary: SeveritySummary
    should_trigger_refinement: bool
    refinement_reason: str = ""
    recommendations: list[str] = Field(default_factory=list)

    def get_critical_issues(self) -> list[QualityIssue]:
        """Get all critical/high severity issues across all examples"""
        issues = []
        for example_issues in self.validation_results.issues_by_example:
            issues.extend([
                i for i in example_issues.issues
                if i.severity in ["critical", "high"]
            ])
        return issues

    def get_issues_for_example(self, example_id: str) -> list[QualityIssue]:
        """Get issues for a specific example"""
        for example_issues in self.validation_results.issues_by_example:
            if example_issues.example_id == example_id:
                return example_issues.issues
        return []

