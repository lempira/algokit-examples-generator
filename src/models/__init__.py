"""Pydantic models for workflow state and phase outputs"""

# Discovery models
from .discovery import DiscoveryResult, DiscoverySummary, TestFile

# Distillation models
from .distillation import (
    ArtifactPlan,
    DistillationResult,
    DistillationSummary,
    EnvironmentVariable,
    ExamplePlan,
    ExamplePrerequisites,
    RefinementHistoryEntry,
    RunInstructions,
    SourceTest,
)

# Extraction models
from .extraction import (
    ExtractionResult,
    ExtractionSummary,
    Prerequisites,
    TestBlock,
    TestFileAnalysis,
)

# Generation models
from .generation import (
    GeneratedArtifact,
    GeneratedExample,
    GenerationResult,
    GenerationSummary,
)

# Quality models
from .quality import (
    ExampleIssues,
    QualityIssue,
    QualityResult,
    SeveritySummary,
    ValidationCheckResult,
    ValidationChecks,
    ValidationResults,
)

# Refinement models
from .refinement import RefinementAction, RefinementResult

# Workflow models
from .workflow import LLMConfig, WorkflowDeps, WorkflowState

__all__ = [
    # Discovery
    "DiscoveryResult",
    "DiscoverySummary",
    "TestFile",
    # Extraction
    "ExtractionResult",
    "ExtractionSummary",
    "Prerequisites",
    "TestBlock",
    "TestFileAnalysis",
    # Distillation
    "ArtifactPlan",
    "DistillationResult",
    "DistillationSummary",
    "EnvironmentVariable",
    "ExamplePlan",
    "ExamplePrerequisites",
    "RefinementHistoryEntry",
    "RunInstructions",
    "SourceTest",
    # Generation
    "GeneratedArtifact",
    "GeneratedExample",
    "GenerationResult",
    "GenerationSummary",
    # Quality
    "ExampleIssues",
    "QualityIssue",
    "QualityResult",
    "SeveritySummary",
    "ValidationCheckResult",
    "ValidationChecks",
    "ValidationResults",
    # Refinement
    "RefinementAction",
    "RefinementResult",
    # Workflow
    "LLMConfig",
    "WorkflowDeps",
    "WorkflowState",
]
