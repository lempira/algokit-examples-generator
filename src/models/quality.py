"""Pydantic models for Quality phase (Phase 5)"""

from datetime import datetime

from pydantic import BaseModel, Field


class ValidationCheckResult(BaseModel):
    """Result of a specific validation check"""

    passed: int = 0
    checks: list[str] = Field(default_factory=list)
    language: str | None = None  # For language_compliance check


class ValidationChecks(BaseModel):
    """All validation checks performed"""

    completeness: ValidationCheckResult = Field(default_factory=ValidationCheckResult)
    api_usage: ValidationCheckResult = Field(default_factory=ValidationCheckResult)
    language_compliance: ValidationCheckResult = Field(default_factory=ValidationCheckResult)
    artifacts: ValidationCheckResult = Field(default_factory=ValidationCheckResult)


class QualityIssue(BaseModel):
    """Represents a quality issue found in an example"""

    type: str = "unknown"  # e.g., "missing_env_var", "type_error", "import_error"
    severity: str = "unknown"  # "critical", "high", "medium", or "low"
    description: str = ""
    recommendation: str = ""
    check: str | None = None  # Which check found this issue


class ExampleIssues(BaseModel):
    """Issues found for a specific example"""

    example_id: str = ""
    issues: list[QualityIssue] = Field(default_factory=list)


class ValidationResults(BaseModel):
    """Detailed validation results"""

    examples_validated: int = 0
    passed: int = 0
    failed: int = 0
    validation_checks: ValidationChecks = Field(default_factory=ValidationChecks)
    issues_by_example: list[ExampleIssues] = Field(default_factory=list)


class SeveritySummary(BaseModel):
    """Summary of issues by severity"""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total: int = 0


class QualityResult(BaseModel):
    """Output from Phase 5: Quality"""

    timestamp: datetime | None = None
    repository: str = ""
    iteration: int = 1
    validation_results: ValidationResults = Field(default_factory=ValidationResults)
    severity_summary: SeveritySummary = Field(default_factory=SeveritySummary)
    should_trigger_refinement: bool = False
    refinement_reason: str = ""
    recommendations: list[str] = Field(default_factory=list)

    def get_critical_issues(self) -> list[QualityIssue]:
        """Get all critical/high severity issues across all examples"""
        issues = []
        for example_issues in self.validation_results.issues_by_example:
            issues.extend([i for i in example_issues.issues if i.severity in ["critical", "high"]])
        return issues

    def get_issues_for_example(self, example_id: str) -> list[QualityIssue]:
        """Get issues for a specific example"""
        for example_issues in self.validation_results.issues_by_example:
            if example_issues.example_id == example_id:
                return example_issues.issues
        return []
