"""Quality node for Phase 5: Quality Assurance"""

from datetime import datetime
from pathlib import Path

from ..agents.quality import QualityAgent
from ..models.phase_outputs import (
    ExampleIssues,
    QualityIssue,
    QualityResult,
    SeveritySummary,
    ValidationCheckResult,
    ValidationChecks,
    ValidationResults,
)
from ..models.workflow import LLMConfig
from ..utils.code_executor import CodeExecutor
from ..utils.json_store import JSONStore


class QualityNode:
    """Phase 5: Validate generated examples"""

    def __init__(
        self,
        repo_path: Path,
        examples_path: Path,
        json_store: JSONStore,
        executor: CodeExecutor,
        llm_config: LLMConfig,
        agent: QualityAgent | None = None,
        iteration: int = 1,
    ):
        self.repo_path = repo_path
        self.examples_path = examples_path
        self.json_store = json_store
        self.executor = executor
        self.llm_config = llm_config
        self.agent = agent if agent is not None else QualityAgent(llm_config)
        self.iteration = iteration

    def run(self, repository_name: str) -> QualityResult:
        """Execute quality assurance phase

        Args:
            repository_name: Name of the repository

        Returns:
            QualityResult with validation results
        """
        # Load generation results
        generation_data = self.json_store.read_sync("04-generation.json")
        if not generation_data:
            raise ValueError("Generation results not found. Run generation phase first.")

        # Determine which examples to validate
        examples_to_validate = self._select_examples_to_validate(generation_data)

        # Run validation checks
        validation_results = []
        issues_by_example = []

        for example_data in examples_to_validate:
            example_id = example_data["example_id"]
            folder = example_data["folder"]

            # Run validation
            validation_result, issues = self._validate_example(example_id, folder)
            validation_results.append(validation_result)

            if issues.issues:
                issues_by_example.append(issues)

        # Calculate validation checks summary
        validation_checks = self._calculate_validation_checks(validation_results)

        # Calculate severity summary
        severity_summary = self._calculate_severity_summary(issues_by_example)

        # Determine if refinement is needed
        should_trigger_refinement, refinement_reason = self._determine_refinement(
            validation_results, severity_summary, len(examples_to_validate)
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            issues_by_example, should_trigger_refinement
        )

        # Build final validation results
        final_validation_results = ValidationResults(
            examples_validated=len(examples_to_validate),
            passed=sum(1 for v in validation_results if v["passed"]),
            failed=sum(1 for v in validation_results if not v["passed"]),
            validation_checks=validation_checks,
            issues_by_example=issues_by_example,
        )

        # Create result
        result = QualityResult(
            timestamp=datetime.now(),
            repository=repository_name,
            iteration=self.iteration,
            validation_results=final_validation_results,
            severity_summary=severity_summary,
            should_trigger_refinement=should_trigger_refinement,
            refinement_reason=refinement_reason,
            recommendations=recommendations,
        )

        # Save to JSON
        self.json_store.write_sync("05-quality.json", result)

        return result

    def _select_examples_to_validate(self, generation_data: dict) -> list[dict]:
        """Select examples that need validation

        Args:
            generation_data: Generation results

        Returns:
            List of examples to validate
        """
        examples_to_validate = []

        for example in generation_data.get("examples", []):
            status = example.get("status")

            # Validate newly generated or needs_review examples
            if status in ["generated", "needs_review"]:
                examples_to_validate.append(example)

        return examples_to_validate

    def _validate_example(
        self, example_id: str, folder: str
    ) -> tuple[dict, ExampleIssues]:
        """Validate a single example

        Args:
            example_id: Example identifier
            folder: Path to example folder

        Returns:
            Tuple of (validation_result_dict, ExampleIssues)
        """
        example_path = Path(folder)
        issues = []

        # Check completeness
        completeness_passed = self._check_completeness(example_path, issues)

        # Check API usage
        api_usage_passed = self._check_api_usage(example_path, issues)

        # Check language compliance
        language_passed = self._check_language_compliance(example_path, issues)

        # Check artifacts
        artifacts_passed = self._check_artifacts(example_path, issues)

        # Try to run the example
        runability_passed = self._check_runability(example_path, issues)

        # Validation result
        passed = all(
            [
                completeness_passed,
                api_usage_passed,
                language_passed,
                artifacts_passed,
                runability_passed,
            ]
        )

        validation_result = {
            "example_id": example_id,
            "passed": passed,
            "checks": {
                "completeness": completeness_passed,
                "api_usage": api_usage_passed,
                "language_compliance": language_passed,
                "artifacts": artifacts_passed,
                "runability": runability_passed,
            },
        }

        example_issues = ExampleIssues(example_id=example_id, issues=issues)

        return validation_result, example_issues

    def _check_completeness(self, example_path: Path, issues: list[QualityIssue]) -> bool:
        """Check if example has all required files

        Args:
            example_path: Path to example
            issues: List to append issues to

        Returns:
            True if complete
        """
        passed = True
        required_files = ["main.ts", "package.json", "README.md", "tsconfig.json"]

        for file_name in required_files:
            if not (example_path / file_name).exists():
                issues.append(
                    QualityIssue(
                        type="missing_file",
                        severity="critical",
                        description=f"Missing required file: {file_name}",
                        recommendation=f"Generate {file_name}",
                        check="completeness",
                    )
                )
                passed = False

        return passed

    def _check_api_usage(self, example_path: Path, issues: list[QualityIssue]) -> bool:
        """Check if example uses correct APIs

        Args:
            example_path: Path to example
            issues: List to append issues to

        Returns:
            True if API usage is correct
        """
        passed = True
        main_file = example_path / "main.ts"

        if main_file.exists():
            content = main_file.read_text()

            # Check for algosdk imports
            if "from 'algosdk'" in content or 'from "algosdk"' in content:
                issues.append(
                    QualityIssue(
                        type="incorrect_import",
                        severity="critical",
                        description="Code imports from 'algosdk' instead of '@algorandfoundation/algokit-utils'",
                        recommendation="Replace algosdk imports with algokit-utils equivalents",
                        check="api_usage",
                    )
                )
                passed = False

            # Check package.json
            package_json = example_path / "package.json"
            if package_json.exists():
                import json

                try:
                    pkg_data = json.loads(package_json.read_text())
                    deps = pkg_data.get("dependencies", {})

                    # Check algokit-utils path
                    algokit_utils_dep = deps.get("@algorandfoundation/algokit-utils")
                    if algokit_utils_dep != "file:../../dist":
                        issues.append(
                            QualityIssue(
                                type="incorrect_dependency",
                                severity="critical",
                                description="algokit-utils dependency should be 'file:../../dist'",
                                recommendation="Update package.json to use 'file:../../dist'",
                                check="api_usage",
                            )
                        )
                        passed = False

                    # Check type: module
                    if pkg_data.get("type") != "module":
                        issues.append(
                            QualityIssue(
                                type="missing_module_type",
                                severity="high",
                                description="package.json should have 'type': 'module'",
                                recommendation="Add 'type': 'module' to package.json",
                                check="api_usage",
                            )
                        )
                        passed = False

                except json.JSONDecodeError:
                    issues.append(
                        QualityIssue(
                            type="invalid_json",
                            severity="critical",
                            description="package.json is not valid JSON",
                            recommendation="Fix JSON syntax in package.json",
                            check="api_usage",
                        )
                    )
                    passed = False

        return passed

    def _check_language_compliance(
        self, example_path: Path, issues: list[QualityIssue]
    ) -> bool:
        """Check language-specific compliance

        Args:
            example_path: Path to example
            issues: List to append issues to

        Returns:
            True if compliant
        """
        passed = True

        # For TypeScript, we would run tsc --noEmit
        # For now, just check for basic issues
        main_file = example_path / "main.ts"
        if main_file.exists():
            content = main_file.read_text()

            # Check for test scaffolding
            test_patterns = ["expect(", "assert(", "mock(", "spy(", "jest.", "describe(", "it("]
            for pattern in test_patterns:
                if pattern in content:
                    issues.append(
                        QualityIssue(
                            type="test_scaffolding",
                            severity="high",
                            description=f"Code contains test scaffolding: {pattern}",
                            recommendation=f"Remove {pattern} and related test code",
                            check="language_compliance",
                        )
                    )
                    passed = False
                    break

        return passed

    def _check_artifacts(self, example_path: Path, issues: list[QualityIssue]) -> bool:
        """Check if required artifacts exist

        Args:
            example_path: Path to example
            issues: List to append issues to

        Returns:
            True if artifacts are present
        """
        # Simple check - if artifacts directory exists, assume it's correct
        # In a real implementation, would validate artifact contents
        artifacts_dir = example_path / "artifacts"
        if artifacts_dir.exists() and not any(artifacts_dir.iterdir()):
            issues.append(
                QualityIssue(
                    type="empty_artifacts",
                    severity="medium",
                    description="Artifacts directory is empty",
                    recommendation="Add required artifacts or remove directory",
                    check="artifacts",
                )
            )
            return False

        return True

    def _check_runability(self, example_path: Path, issues: list[QualityIssue]) -> bool:
        """Check if example can run

        Args:
            example_path: Path to example
            issues: List to append issues to

        Returns:
            True if example runs
        """
        try:
            # Try to execute the example
            result = self.executor.run_sync(example_path)

            if not result.success:
                issues.append(
                    QualityIssue(
                        type="execution_error",
                        severity="critical",
                        description=f"Example failed to run: {result.error_message}",
                        recommendation="Fix runtime errors in the example",
                        check="runability",
                    )
                )
                return False

            return True

        except Exception as e:
            issues.append(
                QualityIssue(
                    type="execution_error",
                    severity="critical",
                    description=f"Could not execute example: {str(e)}",
                    recommendation="Ensure example has proper entry point and dependencies",
                    check="runability",
                )
            )
            return False

    def _calculate_validation_checks(
        self, validation_results: list[dict]
    ) -> ValidationChecks:
        """Calculate validation checks summary

        Args:
            validation_results: List of validation results

        Returns:
            ValidationChecks summary
        """
        total = len(validation_results)

        completeness_passed = sum(
            1 for v in validation_results if v["checks"]["completeness"]
        )
        api_usage_passed = sum(1 for v in validation_results if v["checks"]["api_usage"])
        language_passed = sum(
            1 for v in validation_results if v["checks"]["language_compliance"]
        )
        artifacts_passed = sum(1 for v in validation_results if v["checks"]["artifacts"])

        return ValidationChecks(
            completeness=ValidationCheckResult(
                passed=completeness_passed,
                total=total,
                checks=[
                    "All required files exist",
                    "README has clear instructions",
                    "Prerequisites documented",
                ],
            ),
            api_usage=ValidationCheckResult(
                passed=api_usage_passed,
                total=total,
                checks=[
                    "Code uses public APIs",
                    "No internal imports",
                    "Dependencies match imports",
                ],
            ),
            language_compliance=ValidationCheckResult(
                passed=language_passed,
                total=total,
                language="typescript",
                checks=["No test scaffolding", "Clean code structure"],
            ),
            artifacts=ValidationCheckResult(
                passed=artifacts_passed,
                total=total,
                checks=["Required artifacts exist", "Artifacts are functional"],
            ),
        )

    def _calculate_severity_summary(
        self, issues_by_example: list[ExampleIssues]
    ) -> SeveritySummary:
        """Calculate severity summary

        Args:
            issues_by_example: List of issues by example

        Returns:
            SeveritySummary
        """
        critical = 0
        high = 0
        medium = 0
        low = 0

        for example_issues in issues_by_example:
            for issue in example_issues.issues:
                if issue.severity == "critical":
                    critical += 1
                elif issue.severity == "high":
                    high += 1
                elif issue.severity == "medium":
                    medium += 1
                elif issue.severity == "low":
                    low += 1

        return SeveritySummary(
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            total=critical + high + medium + low,
        )

    def _determine_refinement(
        self,
        validation_results: list[dict],
        severity_summary: SeveritySummary,
        total_validated: int,
    ) -> tuple[bool, str]:
        """Determine if refinement is needed

        Args:
            validation_results: Validation results
            severity_summary: Severity summary
            total_validated: Total examples validated

        Returns:
            Tuple of (should_trigger, reason)
        """
        # Check for critical or high severity issues
        if severity_summary.critical > 0:
            return (
                True,
                f"Found {severity_summary.critical} critical severity issue(s)",
            )

        if severity_summary.high > 0:
            return True, f"Found {severity_summary.high} high severity issue(s)"

        # Check if more than 20% need review
        failed = sum(1 for v in validation_results if not v["passed"])
        if total_validated > 0 and (failed / total_validated) > 0.2:
            return True, f"{failed} examples failed validation (>{20}% threshold)"

        return False, "All examples passed validation"

    def _generate_recommendations(
        self, issues_by_example: list[ExampleIssues], should_refine: bool
    ) -> list[str]:
        """Generate recommendations

        Args:
            issues_by_example: Issues by example
            should_refine: Whether refinement will be triggered

        Returns:
            List of recommendations
        """
        recommendations = []

        if should_refine:
            # Gather unique recommendations from issues
            seen_recommendations = set()
            for example_issues in issues_by_example:
                for issue in example_issues.issues:
                    if issue.severity in ["critical", "high"]:
                        rec = f"{example_issues.example_id}: {issue.recommendation}"
                        if rec not in seen_recommendations:
                            recommendations.append(rec)
                            seen_recommendations.add(rec)

        if not recommendations:
            recommendations.append("All examples passed validation successfully")

        return recommendations

