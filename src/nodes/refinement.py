"""Refinement node for Phase 6: Iterative Refinement"""

from datetime import datetime
from pathlib import Path

from ..agents.refinement import RefinementAgent
from ..models.phase_outputs import RefinementHistoryEntry
from ..models.workflow import LLMConfig
from ..utils.json_store import JSONStore


class RefinementNode:
    """Phase 6: Fix issues found in quality assurance"""

    def __init__(
        self,
        repo_path: Path,
        examples_path: Path,
        json_store: JSONStore,
        llm_config: LLMConfig,
        agent: RefinementAgent | None = None,
        iteration: int = 1,
    ):
        self.repo_path = repo_path
        self.examples_path = examples_path
        self.json_store = json_store
        self.llm_config = llm_config
        self.agent = agent if agent is not None else RefinementAgent(llm_config)
        self.iteration = iteration

    def run(self, repository_name: str) -> RefinementHistoryEntry:
        """Execute refinement phase

        Args:
            repository_name: Name of the repository

        Returns:
            RefinementHistoryEntry with changes applied
        """
        # Load quality results
        quality_data = self.json_store.read_sync("05-quality.json")
        if not quality_data:
            raise ValueError("Quality results not found. Run quality phase first.")

        # Load generation results
        generation_data = self.json_store.read_sync("04-generation.json")
        if not generation_data:
            raise ValueError("Generation results not found.")

        # Get issues to fix
        issues_by_example = quality_data.get("validation_results", {}).get("issues_by_example", [])

        # Count issues before refinement
        issues_before = sum(len(ex["issues"]) for ex in issues_by_example)

        # Apply fixes
        changes_applied = 0
        issues_resolved = []
        examples_updated = []

        for example_issues in issues_by_example:
            example_id = example_issues["example_id"]
            issues = example_issues["issues"]

            # Skip if no critical/high issues
            critical_or_high = [i for i in issues if i["severity"] in ["critical", "high"]]

            if critical_or_high:
                # Apply fixes
                success = self._fix_example(example_id, critical_or_high)

                if success:
                    changes_applied += 1
                    examples_updated.append(example_id)

                    # Record resolved issues
                    for issue in critical_or_high:
                        issues_resolved.append(
                            f"Fixed {issue['type']} in {example_id}: {issue['description']}"
                        )

        # Count issues after refinement (estimate - actual count from next QA run)
        issues_after = max(0, issues_before - len(issues_resolved))

        # Create refinement history entry
        history_entry = RefinementHistoryEntry(
            iteration=self.iteration,
            timestamp=datetime.now(),
            changes_applied=changes_applied,
            issues_resolved=issues_resolved,
            examples_updated=examples_updated,
            issues_before=issues_before,
            issues_after=issues_after,
        )

        # Update distillation data with refinement history
        distillation_data = self.json_store.read_sync("03-distillation.json")
        if distillation_data:
            if "refinement_history" not in distillation_data:
                distillation_data["refinement_history"] = []

            distillation_data["refinement_history"].append(history_entry.model_dump())
            self.json_store.write_sync("03-distillation.json", distillation_data)

        return history_entry

    def _fix_example(self, example_id: str, issues: list[dict]) -> bool:
        """Fix a single example

        Args:
            example_id: Example identifier
            issues: List of issues to fix

        Returns:
            True if fixes were applied successfully
        """
        try:
            # Find example folder
            example_path = None
            for folder in self.examples_path.iterdir():
                if folder.is_dir() and folder.name.startswith(example_id):
                    example_path = folder
                    break

            if not example_path:
                print(f"Warning: Could not find folder for {example_id}")
                return False

            # Read current files
            main_file = example_path / "main.ts"
            readme_file = example_path / "README.md"
            package_file = example_path / "package.json"
            env_file = example_path / ".env.example"

            if not main_file.exists():
                print(f"Warning: main.ts not found for {example_id}")
                return False

            current_main = main_file.read_text()
            current_readme = readme_file.read_text() if readme_file.exists() else ""
            current_package = package_file.read_text() if package_file.exists() else "{}"
            current_env = env_file.read_text() if env_file.exists() else None

            # Use agent to fix issues
            refined = self.agent.refine_example_sync(
                example_id=example_id,
                issues=issues,
                current_main_code=current_main,
                current_readme=current_readme,
                current_package_json=current_package,
                current_env_example=current_env,
            )

            # Write updated files
            if refined.main_code:
                main_file.write_text(refined.main_code)

            if refined.readme_content:
                readme_file.write_text(refined.readme_content)

            if refined.package_json:
                package_file.write_text(refined.package_json)

            if refined.env_example:
                env_file.write_text(refined.env_example)

            return True

        except Exception as e:
            print(f"Error fixing {example_id}: {e}")
            return False
