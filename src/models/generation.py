"""Pydantic models for Generation phase (Phase 4)"""

from datetime import datetime

from pydantic import BaseModel, Field

from .distillation import RefinementHistoryEntry, SourceTest


class GeneratedArtifact(BaseModel):
    """Generated artifact information"""

    target_file: str = ""
    source: str = ""  # "copied" or "generated"
    source_path: str | None = None


class GeneratedExample(BaseModel):
    """Represents a generated example"""

    example_id: str = ""
    title: str = ""
    folder: str = ""
    status: str = "generated"  # "generated", "needs_review", or "error"
    generated_files: list[str] = Field(default_factory=list)
    generated_artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    generation_notes: str = ""
    source_tests: list[SourceTest] = Field(default_factory=list)


class GenerationSummary(BaseModel):
    """Summary statistics for generation phase"""

    total_examples: int = 0
    generated: int = 0
    needs_review: int = 0
    error: int = 0


class GenerationResult(BaseModel):
    """Output from Phase 4: Generation"""

    timestamp: datetime | None = None
    repository: str = ""
    examples: list[GeneratedExample] = Field(default_factory=list)
    summary: GenerationSummary = Field(default_factory=GenerationSummary)
    refinement_history: list[RefinementHistoryEntry] = Field(default_factory=list)

    def get_example(self, example_id: str) -> GeneratedExample | None:
        """Get a specific generated example by ID"""
        return next((e for e in self.examples if e.example_id == example_id), None)

    def get_successful_examples(self) -> list[GeneratedExample]:
        """Get all successfully generated examples"""
        return [e for e in self.examples if e.status == "generated"]
