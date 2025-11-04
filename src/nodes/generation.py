"""Generation node for Phase 4: Example Generation"""

import shutil
from datetime import datetime
from pathlib import Path

from pydantic_ai import Agent

from ..agents import generation
from ..models import (
    GeneratedArtifact,
    GeneratedExample,
    GenerationResult,
    GenerationSummary,
    LLMConfig,
)
from ..utils.file_reader import CodeFileReader
from ..utils.json_store import JSONStore


class GenerationNode:
    """Phase 4: Generate runnable example files"""

    def __init__(
        self,
        repo_path: Path,
        examples_path: Path,
        json_store: JSONStore,
        file_reader: CodeFileReader,
        llm_config: LLMConfig,
        agent: Agent | None = None,
    ):
        self.repo_path = repo_path
        self.examples_path = examples_path
        self.json_store = json_store
        self.file_reader = file_reader
        self.llm_config = llm_config
        self.agent = agent if agent is not None else generation.create_generation_agent(llm_config)

    def run(self, repository_name: str) -> GenerationResult:
        """Execute generation phase

        Args:
            repository_name: Name of the repository

        Returns:
            GenerationResult with generation status
        """
        print("\n=== Phase 4: Generation ===")
        print(f"Repository: {repository_name}")

        # Load distillation results
        print("\nLoading distillation results...")
        distillation_data = self.json_store.read_sync("03-distillation.json")
        if not distillation_data:
            raise ValueError("Distillation results not found. Run distillation phase first.")

        examples_to_generate = distillation_data.get("examples", [])
        print(f"Found {len(examples_to_generate)} examples to generate")

        # Generate all examples
        generated_examples = []

        print("\nGenerating examples:")
        for idx, example_data in enumerate(examples_to_generate, 1):
            example_id = example_data.get("example_id", "unknown")
            title = example_data.get("title", "Untitled")
            complexity = example_data.get("complexity", "unknown")

            complexity_emoji = {"simple": "🟢", "moderate": "🟡", "complex": "🔴"}.get(
                complexity, "⚪"
            )

            print(f"\n  [{idx}/{len(examples_to_generate)}] {complexity_emoji} {title}")
            print(f"      ID: {example_id}")

            # Generate example (all have status="planned")
            result = self._generate_example(example_data, repository_name)
            generated_examples.append(result)

            # Log result
            if result.status == "generated":
                print("      ✅ Generated successfully")
                print(f"         Files: {', '.join(result.generated_files)}")
            elif result.status == "needs_review":
                print("      ⚠️  Generated with warnings - needs review")
            else:
                print("      ❌ Generation failed")
                if result.generation_notes:
                    print(f"         Error: {result.generation_notes[:80]}...")

        # Calculate summary
        summary = self._calculate_summary(generated_examples)

        # Create result
        result = GenerationResult(
            timestamp=datetime.now(),
            repository=repository_name,
            examples=generated_examples,
            summary=summary,
        )

        # Save to JSON
        self.json_store.write_sync("04-generation.json", result)

        # Print summary
        print("\n✅ Generation complete:")
        print(f"   Total examples: {summary.total_examples}")
        print(f"   Generated: {summary.generated} ✅")
        print(f"   Needs review: {summary.needs_review} ⚠️")
        print(f"   Errors: {summary.error} ❌")

        return result

    def _generate_example(self, example_data: dict, repository_name: str) -> GeneratedExample:
        """Generate a single example

        Args:
            example_data: Example plan from distillation
            repository_name: Name of the repository

        Returns:
            GeneratedExample with status
        """
        example_id = example_data["example_id"]

        try:
            # Extract source test code
            source_test_code = self._extract_test_code(example_data.get("source_tests", []))

            # Generate example using agent
            generated = generation.generate_example_sync(
                agent=self.agent,
                example_plan=example_data,
                source_test_code=source_test_code,
            )

            # Create example folder
            example_path = self.examples_path / example_id
            example_path.mkdir(parents=True, exist_ok=True)

            # Write files
            generated_files = []

            # Write main.ts
            (example_path / "main.ts").write_text(generated.main_code)
            generated_files.append("main.ts")

            # Write package.json
            (example_path / "package.json").write_text(generated.package_json)
            generated_files.append("package.json")

            # Write tsconfig.json
            (example_path / "tsconfig.json").write_text(generated.tsconfig_json)
            generated_files.append("tsconfig.json")

            # Write README.md
            (example_path / "README.md").write_text(generated.readme_content)
            generated_files.append("README.md")

            # Write .env.example if present
            if generated.env_example:
                (example_path / ".env.example").write_text(generated.env_example)
                generated_files.append(".env.example")

            # Handle artifacts
            generated_artifacts = self._handle_artifacts(
                example_path, example_data.get("artifacts_plan", [])
            )

            # Create result
            return GeneratedExample(
                example_id=example_id,
                title=example_data["title"],
                status="generated",
                generated_files=generated_files,
                generated_artifacts=generated_artifacts,
                generation_notes="",
                source_tests=example_data.get("source_tests", []),
            )

        except Exception as e:
            # Error during generation
            return GeneratedExample(
                example_id=example_id,
                title=example_data["title"],
                status="error",
                generated_files=[],
                generated_artifacts=[],
                generation_notes=f"Error: {str(e)}",
                source_tests=example_data.get("source_tests", []),
            )

    def _extract_test_code(self, source_tests: list[dict]) -> str:
        """Extract test code from source files

        Args:
            source_tests: List of source test references

        Returns:
            Combined test code
        """
        combined_code = []

        for test_ref in source_tests:
            file_path = test_ref["file"]
            test_name = test_ref["test_name"]

            try:
                # Read test file
                content = self.file_reader.read_sync(file_path)

                # Simple extraction - find test block
                # In a real implementation, this would use AST parsing
                lines = content.split("\n")
                in_test = False
                test_code = []

                for line in lines:
                    if test_name in line and ("test(" in line or "it(" in line):
                        in_test = True

                    if in_test:
                        test_code.append(line)

                        # Simple heuristic - end at closing brace
                        if line.strip().startswith("})"):
                            break

                if test_code:
                    combined_code.append("\n".join(test_code))

            except Exception as e:
                print(f"Warning: Could not extract test code from {file_path}: {e}")
                continue

        return "\n\n".join(combined_code) if combined_code else "// No test code found"

    def _handle_artifacts(
        self, example_path: Path, artifacts_plan: list[dict]
    ) -> list[GeneratedArtifact]:
        """Handle artifact copying or generation

        Args:
            example_path: Path to example folder
            artifacts_plan: List of artifact plans

        Returns:
            List of generated artifacts
        """
        generated_artifacts = []

        if not artifacts_plan:
            return generated_artifacts

        # Create artifacts directory
        artifacts_dir = example_path / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        for artifact_plan in artifacts_plan:
            target_file = artifact_plan["target_file"]
            action = artifact_plan["action"]
            source_path = artifact_plan.get("source_path")

            try:
                target_path = artifacts_dir / Path(target_file).name

                if action == "copy" and source_path:
                    # Copy existing artifact
                    source_full_path = self.repo_path / source_path
                    if source_full_path.exists():
                        shutil.copy2(source_full_path, target_path)
                        generated_artifacts.append(
                            GeneratedArtifact(
                                path=f"artifacts/{Path(target_file).name}",
                                type=artifact_plan.get("type", "file"),
                                source="copied",
                            )
                        )

                elif action == "generate":
                    # Generate minimal artifact
                    content = self._generate_minimal_artifact(artifact_plan.get("type", "file"))
                    target_path.write_text(content)
                    generated_artifacts.append(
                        GeneratedArtifact(
                            path=f"artifacts/{Path(target_file).name}",
                            type=artifact_plan.get("type", "file"),
                            source="generated",
                        )
                    )

            except Exception as e:
                print(f"Warning: Could not handle artifact {target_file}: {e}")
                continue

        return generated_artifacts

    def _generate_minimal_artifact(self, artifact_type: str) -> str:
        """Generate minimal but functional artifact

        Args:
            artifact_type: Type of artifact (contract, config, etc.)

        Returns:
            Artifact content as string
        """
        if artifact_type == "contract":
            # Minimal TEAL approval program
            return """#pragma version 8

// Minimal approval program
// Approves all transactions

int 1
return
"""
        elif artifact_type == "config":
            # Minimal JSON config
            return """{
  "version": "1.0",
  "description": "Example configuration"
}
"""
        else:
            # Generic placeholder
            return "# Placeholder artifact\n"

    def _calculate_summary(self, examples: list[GeneratedExample]) -> GenerationSummary:
        """Calculate summary statistics

        Args:
            examples: List of generated examples

        Returns:
            GenerationSummary
        """
        generated = sum(1 for e in examples if e.status == "generated")
        needs_review = sum(1 for e in examples if e.status == "needs_review")
        error = sum(1 for e in examples if e.status == "error")

        return GenerationSummary(
            total_examples=len(examples),
            generated=generated,
            needs_review=needs_review,
            error=error,
        )
