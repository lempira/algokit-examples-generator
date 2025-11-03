"""Pydantic models for Extraction phase (Phase 2)"""

from datetime import datetime

from pydantic import BaseModel, Field


class Prerequisites(BaseModel):
    """Prerequisites for running a test block"""

    imports: list[str] | None = Field(
        None,
        description="List of import statements or dependencies needed (e.g., ['algosdk', 'vitest'])",
    )
    setup_requirements: list[str] | None = Field(
        None,
        description="Setup steps or functions that must be run before this test (e.g., ['algorandFixture()', 'waitForIndexer()'])",
    )
    configuration: list[str] | None = Field(
        None,
        description="Configuration or environment variables needed (e.g., ['ALGOD_TOKEN', 'INDEXER_SERVER'])",
    )


class TestBlock(BaseModel):
    """Represents an extracted test block from a test file"""

    test_name: str | None = Field(
        None,
        description="The exact test name string from the test() or it() call. Extract the literal string, e.g., 'Deploy new app' from test('Deploy new app', ...)",
    )
    source_code: str | None = Field(
        None,
        description="The complete source code for this test, including all nested describe/context blocks and the test implementation. Include the full code from the opening to closing brace.",
    )
    features_tested: list[str] | None = Field(
        None,
        description="List of main APIs, methods, or features being tested in this test block. Include class names and method calls (e.g., ['algorand.appDeployer.deploy', 'algorand.send.appCreate'])",
    )
    feature_classification: str | None = Field(
        None,
        description="Classify the test focus: 'user-facing' if it demonstrates SDK/API usage for developers, 'internal' if testing implementation details, or 'mixed' for both. For SDK tests, default to 'user-facing'.",
    )
    use_case_category: str | None = Field(
        None,
        description="High-level category of the use case being tested (e.g., 'app deployment', 'transaction management', 'error handling'). Only provide if feature_classification is 'user-facing' or 'mixed'.",
    )
    specific_use_case: str | None = Field(
        None,
        description="Concrete, specific scenario being tested (e.g., 'Deploy a new app with metadata', 'Update an immutable app and expect failure'). Only provide if feature_classification is 'user-facing' or 'mixed'.",
    )
    target_users: list[str] | None = Field(
        None,
        description="Types of users/developers who would benefit from this example (e.g., ['SDK developers', 'Smart contract developers', 'DevOps engineers']). Only provide if feature_classification is 'user-facing' or 'mixed'.",
    )
    complexity: str | None = Field(
        None,
        description="Assess test complexity: 'simple' if <30 lines with straightforward logic, 'moderate' if 30-60 lines with some setup, 'complex' if >60 lines or involves multiple components.",
    )
    example_potential: str | None = Field(
        None,
        description="Rate the potential for this test to become a useful example: 'high' if it demonstrates common/essential SDK usage, 'medium' if it shows specialized but useful patterns, 'low' if it's an edge case or implementation detail.",
    )
    key_concepts: list[str] | None = Field(
        None,
        description="Main technical concepts or patterns demonstrated in this test (e.g., ['app deployment', 'metadata management', 'error handling', 'idempotency'])",
    )
    user_value: str | None = Field(
        None,
        description="Brief explanation of why this test/example would help end users/developers. What problem does it solve? Only provide if feature_classification is 'user-facing' or 'mixed'.",
    )
    prerequisites: Prerequisites | None = Field(
        None,
        description="Prerequisites for running this test block",
    )


class TestFileAnalysis(BaseModel):
    """Analysis of a single test file"""

    source_file: str = ""
    test_blocks: list[TestBlock] = Field(default_factory=list)


class ExtractionSummary(BaseModel):
    """Summary statistics for extraction phase"""

    total_test_blocks: int = 0


class ExtractionResult(BaseModel):
    """Output from Phase 2: Extraction - Contains all extracted test blocks"""

    timestamp: datetime | None = None
    repository: str = ""
    summary: ExtractionSummary = Field(default_factory=ExtractionSummary)
    test_analysis: list[TestFileAnalysis] = Field(default_factory=list)
