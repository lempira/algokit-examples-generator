"""Workflow state and dependencies"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..utils.code_executor import CodeExecutor
    from ..utils.file_reader import CodeFileReader
    from ..utils.json_store import JSONStore

from .phase_outputs import (
    DiscoveryResult,
    DistillationResult,
    ExtractionResult,
    GenerationResult,
    QualityResult,
)


@dataclass
class WorkflowState:
    """Shared state across all workflow phases"""

    # Phase outputs (accumulate as workflow progresses)
    discovery_data: DiscoveryResult | None = None
    extraction_data: ExtractionResult | None = None
    distillation_data: DistillationResult | None = None
    generation_data: GenerationResult | None = None
    quality_data: QualityResult | None = None

    # Iteration tracking
    refinement_iteration: int = 0
    max_refinement_iterations: int = 3

    # Metadata
    test_files_changed: list[str] = field(default_factory=list)
    workflow_start_time: datetime = field(default_factory=datetime.now)

    # Runtime context
    is_incremental_run: bool = False


@dataclass
class LLMConfig:
    """Configuration for LLM models"""
    default_model: str = "anthropic:claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int | None = None


@dataclass
class WorkflowDeps:
    """Dependencies shared across all agents and nodes"""

    # Paths
    repo_path: Path
    examples_output_path: Path

    # Utilities (will be defined in utils/)
    file_reader: "CodeFileReader"  # type: ignore
    json_store: "JSONStore"  # type: ignore
    executor: "CodeExecutor"  # type: ignore

    # Configuration
    llm_config: LLMConfig

    # Optional: Progress tracking
    progress_callback: Callable[[str, int], None] | None = None

