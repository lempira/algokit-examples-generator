"""Pydantic models for Refinement phase (Phase 6)"""

from datetime import datetime

from pydantic import BaseModel, Field

from .distillation import RefinementHistoryEntry


class RefinementAction(BaseModel):
    """Represents a single refinement action to be applied"""

    example_id: str = ""
    issue_type: str = ""
    action: str = ""  # "fix", "update", "add", "remove"
    target_file: str | None = None
    changes: str = ""
    rationale: str = ""


class RefinementResult(BaseModel):
    """Output from Phase 6: Refinement"""

    timestamp: datetime | None = None
    repository: str = ""
    iteration: int = 1
    actions_applied: list[RefinementAction] = Field(default_factory=list)
    examples_updated: list[str] = Field(default_factory=list)
    issues_resolved: list[str] = Field(default_factory=list)
    refinement_history: list[RefinementHistoryEntry] = Field(default_factory=list)
